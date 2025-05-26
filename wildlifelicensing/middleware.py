import hashlib
import logging
import re
from urllib.parse import quote_plus

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from reversion.middleware import RevisionMiddleware
from reversion.views import _request_creates_revision

from wildlifelicensing.apps.applications.models import Application
from wildlifelicensing.apps.main.helpers import is_internal

logger = logging.getLogger(__name__)


CHECKOUT_PATH = re.compile("^/ledger/checkout/checkout")


class FirstTimeNagScreenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            not request.user.is_authenticated
            or not request.method == "GET"
            or "api" in request.path
            or "admin" in request.path
            or "static" in request.path
        ):
            return self.get_response(request)

        if (
            request.user.first_name
            and request.user.last_name
            # Don't require internal users to fill in phone numbers
            and is_internal(request)
            or (request.user.phone_number or request.user.mobile_number)
        ):
            return self.get_response(request)

        path_ft = reverse("account-firstime")
        if request.path in ("/sso/setting", path_ft, reverse("logout")):
            return self.get_response(request)

        return redirect(path_ft + "?next=" + quote_plus(request.get_full_path()))


class CacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path[:5] == "/api/" or request.path == "/":
            response["Cache-Control"] = "private, no-store"
        elif request.path[:8] == "/static/":
            response["Cache-Control"] = "public, max-age=300"
        return response


def payment_session_redirect_response():
    url_redirect = reverse("home")
    return HttpResponse(
        f"<script> window.location='{url_redirect}';</script> "
        "<center><div class='container'><div class='alert alert-primary' role='alert'>"
        f"<a href='{url_redirect}'> Redirecting please wait: {url_redirect}</a><div></div></center>"
    )


class RevisionOverrideMiddleware(RevisionMiddleware):
    """
    Wraps the entire request in a revision.

    override venv/lib/python2.7/site-packages/reversion/middleware.py
    """

    # exclude ledger payments/checkout from revision -
    # hack to overcome basket (lagging status) issue/conflict with reversion
    def request_creates_revision(self, request):
        return (
            _request_creates_revision(request)
            and "checkout" not in request.get_full_path()
        )


class PaymentSessionMiddleware:
    PROCESS_PAYMENT_PATH_PREFIX = "/ledger-api/process-payment"
    PAYMENT_DETAILS_PATH_PREFIX = "/ledger-api/payment-details"
    PAYMENT_MODEL_KEY = "payment_model"
    PAYMENT_PK_KEY = "payment_pk"

    def __init__(self, get_response: callable) -> None:
        self.get_response = get_response

    def process_view(
        self,
        request: HttpRequest,
        view_func: callable,
        view_args: list,
        view_kwargs: dict,
    ) -> HttpResponse | None:
        if not request.user.is_authenticated:
            return None

        if not (
            CHECKOUT_PATH.match(request.path)
            or request.path.startswith(self.PROCESS_PAYMENT_PATH_PREFIX)
            or request.path.startswith(self.PAYMENT_DETAILS_PATH_PREFIX)
        ):
            return None

        if (
            self.PAYMENT_MODEL_KEY in request.session
            and self.PAYMENT_PK_KEY in request.session
        ):
            if request.path.startswith(self.PROCESS_PAYMENT_PATH_PREFIX):
                checkouthash = hashlib.sha256(
                    str(
                        str(request.session[self.PAYMENT_MODEL_KEY])
                        + str(request.session[self.PAYMENT_PK_KEY])
                    ).encode("utf-8")
                ).hexdigest()
                checkouthash_cookie = request.COOKIES.get("checkouthash")
                validation_cookie = request.COOKIES.get(
                    request.POST["payment-csrfmiddlewaretoken"]
                )

                proposal_exists = False
                if request.session.get(self.PAYMENT_MODEL_KEY, None) == "application":
                    proposal_exists = Application.objects.filter(
                        pk=request.session[self.PAYMENT_PK_KEY]
                    ).exists()

                if (
                    checkouthash_cookie != checkouthash
                    or checkouthash_cookie != validation_cookie
                    or not proposal_exists
                ):
                    return payment_session_redirect_response()
        else:
            if request.path.startswith(self.PROCESS_PAYMENT_PATH_PREFIX):
                return payment_session_redirect_response()

        return None

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if not request.user.is_authenticated:
            return response

        if not (
            CHECKOUT_PATH.match(request.path)
            or request.path.startswith(self.PROCESS_PAYMENT_PATH_PREFIX)
            or request.path.startswith(self.PAYMENT_DETAILS_PATH_PREFIX)
        ):
            return response

        if (
            self.PAYMENT_MODEL_KEY in request.session
            and self.PAYMENT_PK_KEY in request.session
        ):
            proposal_exists = False
            if request.session.get(self.PAYMENT_MODEL_KEY, None) == "application":
                proposal_exists = Application.objects.filter(
                    pk=request.session[self.PAYMENT_PK_KEY]
                ).exists()

            if not proposal_exists:
                del request.session[self.PAYMENT_MODEL_KEY]
                del request.session[self.PAYMENT_PK_KEY]
                return response

            if request.path.startswith(self.PROCESS_PAYMENT_PATH_PREFIX):
                if self.PAYMENT_PK_KEY not in request.session:
                    return payment_session_redirect_response()

                checkouthash = hashlib.sha256(
                    str(
                        str(request.session[self.PAYMENT_MODEL_KEY])
                        + str(request.session[self.PAYMENT_PK_KEY])
                    ).encode("utf-8")
                ).hexdigest()
                checkouthash_cookie = request.COOKIES.get("checkouthash")
                validation_cookie = request.COOKIES.get(
                    request.POST["payment-csrfmiddlewaretoken"]
                )

                proposal_exists = False
                if request.session.get(self.PAYMENT_MODEL_KEY, None) == "application":
                    proposal_exists = Application.objects.filter(
                        pk=request.session[self.PAYMENT_PK_KEY]
                    ).exists()

                if (
                    checkouthash_cookie != checkouthash
                    or checkouthash_cookie != validation_cookie
                    or not proposal_exists
                ):
                    return payment_session_redirect_response()
        else:
            if request.path.startswith(self.PROCESS_PAYMENT_PATH_PREFIX):
                return payment_session_redirect_response()

        # force a redirect if in the checkout
        if (
            self.PAYMENT_PK_KEY not in request.session
            or self.PAYMENT_MODEL_KEY not in request.session
        ) and CHECKOUT_PATH.match(request.path):
            return payment_session_redirect_response()

        return response
