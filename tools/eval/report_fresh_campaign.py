"""Checkout CLI facade; delivery logic belongs to the installable application."""
from uc3m.application.evaluation.fresh_delivery import (
    DeliveryCheck, build_fresh_delivery, verify_delivery, main,
)

__all__ = ['DeliveryCheck', 'build_fresh_delivery', 'verify_delivery', 'main']

if __name__ == '__main__':
    raise SystemExit(main())
