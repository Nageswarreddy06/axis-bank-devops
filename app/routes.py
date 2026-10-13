import secrets
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from .extensions import db
from .models import Account, Transaction, User

api = Blueprint("api", __name__, url_prefix="/api")
CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("9999999999.99")


def _error(message, status=400):
    return jsonify({"error": message}), status


def _parse_amount(raw):
    if raw is None or isinstance(raw, bool):
        raise ValueError("Enter a valid amount.")
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Enter a valid amount.")
    if not amount.is_finite():
        raise ValueError("Enter a valid amount.")
    rounded = amount.quantize(CENT)
    if amount != rounded:
        raise ValueError("Amount can have at most two decimal places.")
    if rounded <= Decimal("0.00"):
        raise ValueError("Amount must be greater than zero.")
    if rounded > MAX_AMOUNT:
        raise ValueError("Amount is too large.")
    return rounded


def _new_account_number():
    return f"AXIS{secrets.randbelow(10**10):010d}"


def _new_transaction_id():
    return f"TXN{secrets.token_hex(6).upper()}"


def _current_user_id():
    return int(get_jwt_identity())


def _current_account(lock=False):
    query = Account.query.filter_by(user_id=_current_user_id(), status="ACTIVE")
    if lock:
        query = query.with_for_update()
    return query.first()


def _money(value):
    return f"{Decimal(value):.2f}"


@api.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not full_name or len(full_name) > 120:
        return _error("Enter a full name (maximum 120 characters).")
    if "@" not in email or len(email) > 255:
        return _error("Enter a valid email address.")
    if not isinstance(password, str) or len(password) < 8:
        return _error("Password must contain at least 8 characters.")
    if User.query.filter_by(email=email).first():
        return _error("An account with this email already exists.", 409)

    user = User(full_name=full_name, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.flush()
        account = Account(
            account_number=_new_account_number(),
            user_id=user.id,
            balance=Decimal("0.00"),
            status="ACTIVE",
        )
        db.session.add(account)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Could not create the account. Please try again.", 409)

    return jsonify({
        "message": "Demo account created successfully.",
        "customer": {"id": user.id, "full_name": user.full_name, "email": user.email},
        "account_number": account.account_number,
        "balance": _money(account.balance),
    }), 201


@api.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    user = User.query.filter_by(email=email).first()

    if not user or not isinstance(password, str) or not check_password_hash(user.password_hash, password):
        return _error("Invalid email or password.", 401)

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in_minutes": 30,
    }), 200


@api.get("/account")
@jwt_required()
def account_details():
    account = _current_account()
    if not account:
        return _error("Account not found.", 404)
    return jsonify({
        "account_number": account.account_number,
        "customer": account.owner.full_name,
        "email": account.owner.email,
        "balance": _money(account.balance),
        "status": account.status,
    })


@api.get("/balance")
@jwt_required()
def balance():
    account = _current_account()
    if not account:
        return _error("Account not found.", 404)
    return jsonify({
        "account_number": account.account_number,
        "balance": _money(account.balance),
        "currency": "INR",
    })


@api.post("/deposit")
@jwt_required()
def deposit():
    data = request.get_json(silent=True) or {}
    try:
        amount = _parse_amount(data.get("amount"))
    except ValueError as exc:
        return _error(str(exc))

    account = _current_account(lock=True)
    if not account:
        return _error("Account not found.", 404)

    account.balance = Decimal(account.balance) + amount
    transaction = Transaction(
        transaction_id=_new_transaction_id(),
        from_account_id=None,
        to_account_id=account.id,
        transaction_type="DEPOSIT",
        amount=amount,
        status="SUCCESS",
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({
        "message": "Demo deposit successful.",
        "transaction_id": transaction.transaction_id,
        "amount": _money(amount),
        "balance": _money(account.balance),
    }), 201


@api.post("/withdraw")
@jwt_required()
def withdraw():
    data = request.get_json(silent=True) or {}
    try:
        amount = _parse_amount(data.get("amount"))
    except ValueError as exc:
        return _error(str(exc))

    account = _current_account(lock=True)
    if not account:
        return _error("Account not found.", 404)
    if Decimal(account.balance) < amount:
        return _error("Insufficient balance.", 400)

    account.balance = Decimal(account.balance) - amount
    transaction = Transaction(
        transaction_id=_new_transaction_id(),
        from_account_id=account.id,
        to_account_id=None,
        transaction_type="WITHDRAWAL",
        amount=amount,
        status="SUCCESS",
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({
        "message": "Demo withdrawal successful.",
        "transaction_id": transaction.transaction_id,
        "amount": _money(amount),
        "balance": _money(account.balance),
    }), 201


@api.post("/transfer")
@jwt_required()
def transfer():
    data = request.get_json(silent=True) or {}
    target_number = str(data.get("to_account", "")).strip().upper()
    try:
        amount = _parse_amount(data.get("amount"))
    except ValueError as exc:
        return _error(str(exc))
    if not target_number:
        return _error("Enter the destination account number.")

    source_candidate = _current_account()
    target_candidate = Account.query.filter_by(
        account_number=target_number, status="ACTIVE"
    ).first()
    if not source_candidate:
        return _error("Source account not found.", 404)
    if not target_candidate:
        return _error("Destination account not found.", 404)
    if source_candidate.id == target_candidate.id:
        return _error("You cannot transfer to the same account.")

    # Lock both accounts in a consistent ID order to reduce deadlock risk.
    locked = Account.query.filter(
        Account.id.in_([source_candidate.id, target_candidate.id])
    ).order_by(Account.id).with_for_update().all()
    by_id = {account.id: account for account in locked}
    source = by_id.get(source_candidate.id)
    target = by_id.get(target_candidate.id)
    if not source or not target:
        db.session.rollback()
        return _error("Could not lock the accounts. Please try again.", 409)
    if Decimal(source.balance) < amount:
        db.session.rollback()
        return _error("Insufficient balance.", 400)

    source.balance = Decimal(source.balance) - amount
    target.balance = Decimal(target.balance) + amount
    transaction = Transaction(
        transaction_id=_new_transaction_id(),
        from_account_id=source.id,
        to_account_id=target.id,
        transaction_type="TRANSFER",
        amount=amount,
        status="SUCCESS",
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({
        "message": "Demo transfer successful.",
        "transaction_id": transaction.transaction_id,
        "to_account": target.account_number,
        "amount": _money(amount),
        "balance": _money(source.balance),
    }), 201


@api.get("/transactions")
@jwt_required()
def transactions():
    account = _current_account()
    if not account:
        return _error("Account not found.", 404)

    rows = Transaction.query.filter(
        or_(
            Transaction.from_account_id == account.id,
            Transaction.to_account_id == account.id,
        )
    ).order_by(Transaction.id.desc()).limit(100).all()

    result = []
    for row in rows:
        direction = "CREDIT" if row.to_account_id == account.id else "DEBIT"
        result.append({
            "transaction_id": row.transaction_id,
            "type": row.transaction_type,
            "direction": direction,
            "amount": _money(row.amount),
            "status": row.status,
            "created_at": row.created_at.isoformat(),
        })
    return jsonify({"transactions": result, "count": len(result)})
