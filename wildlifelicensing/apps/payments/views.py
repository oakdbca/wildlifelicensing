import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic.base import RedirectView, View
from ledger_api_client.utils import create_basket_session, create_checkout_session

from wildlifelicensing.apps.applications.models import Application
from wildlifelicensing.apps.main.helpers import is_officer
from wildlifelicensing.apps.payments.forms import PaymentsReportForm
from wildlifelicensing.apps.payments.utils import generate_product_title, get_product

JSON_REQUEST_HEADER_PARAMS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


logger = logging.getLogger(__name__)


class CheckoutApplicationView(LoginRequiredMixin, RedirectView):
    def get(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=args[0])
        product_title = generate_product_title(application)
        product = get_product(product_title)

        error_url = request.build_absolute_uri(reverse("wl_applications:preview"))
        success_url = request.build_absolute_uri(reverse("wl_applications:complete"))

        products = [
            {
                "ledger_description": product_title,
                "quantity": 1,
                "price_excl_tax": str(product.price),
                "price_incl_tax": str(product.price),
                "oracle_code": product.oracle_code,
                "line_status": settings.LEDGER_DEFAULT_LINE_STATUS,
            }
        ]

        if application.applicant.is_senior:
            discount = product.price * Decimal(
                "0.1"
            )  # TODO: What type of discount do seniors get?
            products.append(
                {
                    "ledger_description": "Senior Discount",
                    "quantity": 1,
                    "price_excl_tax": str(-abs(discount)),
                    "price_incl_tax": str(-abs(discount)),
                    "oracle_code": settings.SENIOR_VOUCHER_ORACLE_CODE,
                    "line_status": settings.LEDGER_DEFAULT_LINE_STATUS,
                }
            )

        booking_reference = f"wl-app-{application.id}"

        basket_params = {
            "products": products,
            "vouchers": [],
            "system": settings.PAYMENT_SYSTEM_PREFIX,
            "custom_basket": True,
            "tax_override": True,
            "no_payment": False,
            "booking_reference": booking_reference,
        }

        logger.info("Creating basket session with params: %s", basket_params)

        create_basket_session(
            request,
            application.applicant.id,
            basket_params,
        )

        checkout_params = {
            "system": settings.PAYMENT_SYSTEM_ID,
            "fallback_url": error_url,
            "return_url": success_url,
            "return_preload_url": success_url,
            "force_redirect": True,
            "proxy": is_officer(request.user),
            "invoice_text": booking_reference,
            "session_type": "ledger_api",
            "basket_owner": request.user.id,
        }

        logger.info("Creating checkout session with params: %s", checkout_params)

        create_checkout_session(request, checkout_params)

        logger.info("Redirecting user to ledgergw payment details page.")
        return redirect(reverse("ledgergw-payment-details"))


class ManualPaymentView(LoginRequiredMixin, RedirectView):
    def get(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=args[0])

        # url = reverse('payments:invoice-payment', args=(application.invoice_reference,))
        url = "{}?invoice={}".format(
            reverse("wl_payments:invoice-payment"), application.invoice_reference
        )

        params = {"redirect_url": request.GET.get("redirect_url", reverse("wl_home"))}

        return redirect(f"{url}&{urlencode(params)}")


class PaymentsReportView(LoginRequiredMixin, View):
    success_url = reverse_lazy("wl_reports:reports")
    error_url = success_url

    def get(self, request):
        form = PaymentsReportForm(request.GET)
        if form.is_valid():
            start = form.cleaned_data.get("start")
            end = form.cleaned_data.get("end")
            banked_start = form.cleaned_data.get("banked_start")
            banked_end = form.cleaned_data.get("banked_end")
            # here start and end should be timezone aware (with the settings.TIME_ZONE
            start = (
                timezone.make_aware(start) if not timezone.is_aware(start) else start
            )
            end = timezone.make_aware(end) if not timezone.is_aware(end) else end
            banked_start = (
                timezone.make_aware(banked_start)
                if not timezone.is_aware(banked_start)
                else banked_start
            )
            banked_end = (
                timezone.make_aware(banked_end)
                if not timezone.is_aware(banked_end)
                else banked_end
            )

            url = request.build_absolute_uri(reverse("wl_payments:ledger-report"))
            data = {
                "system": settings.PAYMENT_SYSTEM_ID,
                "start": start,
                "end": end,
                "banked_start": banked_start,
                "banked_end": banked_end,
            }
            if "items" in request.GET:
                data["items"] = True
            response = requests.get(
                url,
                headers=JSON_REQUEST_HEADER_PARAMS,
                cookies=request.COOKIES,
                params=data,
                verify=False,
            )
            if response.status_code == 200:
                filename = "wl_payments-{}_{}".format(
                    str(start.date()), str(end.date())
                )
                response = HttpResponse(
                    response, content_type="text/csv; charset=utf-8"
                )
                response["Content-Disposition"] = f"attachment; filename={filename}.csv"
                return response
            else:
                messages.error(
                    request,
                    f"There was an error while generating the payment report:<br>{response.content}",
                )
                return redirect(self.error_url)
        else:
            messages.error(request, form.errors)
            return redirect(self.error_url)
