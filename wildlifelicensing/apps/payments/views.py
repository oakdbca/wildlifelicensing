import logging
import uuid
from datetime import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic.base import RedirectView, View
from ledger_api_client.ledger_models import Invoice
from ledger_api_client.utils import create_basket_session, create_checkout_session
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from wildlifelicensing.apps.applications.models import Application
from wildlifelicensing.apps.main.helpers import is_officer
from wildlifelicensing.apps.payments.forms import PaymentsReportForm
from wildlifelicensing.apps.payments.utils import (
    generate_product_title,
    get_ledger_invoice_pdf,
    get_product,
)

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

        # Create a uuid to identify the application so that users can't guess a sequential id
        application.payment_uuid = uuid.uuid4()
        application.save()

        fallback_url = request.build_absolute_uri(reverse("wl_applications:preview"))
        return_url = request.GET.get(
            "redirect_url",
            request.build_absolute_uri(reverse("wl_applications:complete")),
        )

        # Rather than using build_absolute_uri here we are using a pre configured host from the settings
        # as otherwise when an internal user does a proxy application the return_preload_url
        # will be the internal url which will not allow the request due to the sso login mechanism
        return_preload_url = settings.NOTIFICATION_HOST + reverse(
            "wl_payments:ledger-api-payment-success-callback",
            kwargs={"payment_uuid": application.payment_uuid},
        )

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

        if (
            application.licence_type.senior_applicable
            and product.is_discountable
            and application.applicant.is_senior
        ):
            discount = Decimal(product.price * Decimal("0.1")).quantize(
                Decimal("0.00")
            )  # Note: Currently I have just hardcoded the discount to 10% of the product price
            # However, I have found that none of the licences currently being offered allow for a senior discount
            # so this shouldn't actually happen in practice
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
        now_timestamp = str(datetime.timestamp(timezone.now())).replace(".", "-")
        booking_reference = f"wl-app-{application.id}-{now_timestamp}"

        basket_params = {
            "products": products,
            "vouchers": [],
            "system": settings.PAYMENT_SYSTEM_PREFIX,
            "custom_basket": True,
            "tax_override": True,
            "no_payment": product.price == Decimal("0.00"),
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
            "fallback_url": fallback_url,
            "return_url": return_url,
            "return_preload_url": return_preload_url,
            "force_redirect": True,
            "proxy": False,  # When user ledger api client, this doesn't need to be set to True
            # even if it is in fact a proxy application
            "invoice_text": booking_reference,
            "session_type": "ledger_api",
            "basket_owner": application.applicant.id,
        }

        logger.info("Creating checkout session with params: %s", checkout_params)

        create_checkout_session(request, checkout_params)

        request.session["payment_pk"] = application.pk
        request.session["payment_model"] = "application"

        logger.info("Redirecting user to ledgergw payment details page.")
        return redirect(reverse("ledgergw-payment-details"))


class ManualPaymentView(LoginRequiredMixin, RedirectView):
    """ """

    def get(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=args[0])

        url = reverse(
            "wl_payments:checkout_application",
            args=[application.id],
        )

        params = {"redirect_url": request.GET.get("redirect_url", reverse("wl_home"))}

        return redirect(f"{url}?{urlencode(params)}")


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


class PaymentSuccessView(APIView):
    throttle_classes = [AnonRateThrottle]
    renderer_classes = [JSONRenderer]

    def get(self, request, payment_uuid, format=None):
        logger.info("Wildlife Licensing SuccessView get method called.")

        invoice_reference = request.GET.get("invoice", None)

        if not payment_uuid or not invoice_reference:
            # If there isn't a payment_uuid or invoice_reference then send a bad request status back in case ledger can
            # do something with this in future
            logger.info(
                "Returning status.HTTP_400_BAD_REQUEST bad request as both payment_uuid and invoice_reference."
            )

            return Response(status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            f"payment_uuid: {payment_uuid}, invoice_reference: {invoice_reference}.",
        )

        try:
            application = Application.objects.get(payment_uuid=uuid.UUID(payment_uuid))
        except Application.DoesNotExist:
            logger.info(
                f"Returning status.HTTP_404_NOT_FOUND. Application not found with payment_uuid: {payment_uuid}.",
            )
            return Response(status=status.HTTP_404_NOT_FOUND)

        logger.info(f"Setting invoice reference for application id: {application.id}.")

        application.invoice_reference = invoice_reference
        application.save()

        logger.info(
            "Returning status.HTTP_200_OK. Order created successfully.",
        )
        # this end-point is called by an unmonitored get request in ledger so there is no point having a
        # a response body however we will return a status in case this is used on the ledger end in future
        return Response(status=status.HTTP_200_OK)


class InvoicePDFView(LoginRequiredMixin, View):
    def get(self, request, invoice_reference):
        invoice = get_object_or_404(Invoice, reference=invoice_reference)
        if not is_officer(request.user) and invoice.owner.id != request.user.id:
            return HttpResponseNotFound()
        ledger_invoice_pdf = get_ledger_invoice_pdf(invoice_reference)
        return HttpResponse(ledger_invoice_pdf.content, content_type="application/pdf")
