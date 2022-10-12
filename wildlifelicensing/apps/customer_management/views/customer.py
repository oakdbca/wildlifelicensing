from django.contrib import messages
from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse

from wildlifelicensing.apps.dashboard.views import base
from wildlifelicensing.apps.dashboard.views.officer import TablesApplicationsOfficerView, TablesLicencesOfficerView, \
    TablesReturnsOfficerView
from wildlifelicensing.apps.main.mixins import OfficerRequiredMixin
from wildlifelicensing.apps.main.signals import identification_uploaded
from wildlifelicensing.apps.customer_management.forms import CustomerDetailsForm

from ledger.accounts.models import EmailUser, Profile, Document, PrivateDocument
from ledger.accounts.forms import ProfileForm, AddressForm
from wildlifelicensing.apps.main.forms import CommunicationsLogEntryForm


class CustomerLookupView(TablesApplicationsOfficerView, TablesLicencesOfficerView, TablesReturnsOfficerView):
    template_name = 'wl/customer_lookup.html'
    login_url = '/'


    def _build_data(self):
        data = super(CustomerLookupView, self)._build_data()

        # applications
        data['applications']['columnDefinitions'] = [
            {
                'title': 'Lodgement Number'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'User'
            },
            {
                'title': 'Status',
            },
            {
                'title': 'Lodged on'
            },
            {
                'title': 'Assignee'
            },
            {
                'title': 'Proxy'
            },
            {
                'title': 'Payment',
                'searchable': False,
                'orderable': False
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]

        data['applications']['ajax']['url'] = reverse('wl_customer_management:data_applications', args=self.args)
        # global table options
        data['applications']['tableOptions'] = {
            'pageLength': 10
        }

        # licences
        data['licences']['columnDefinitions'] = [
            {
                'title': 'Licence Number'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'User'
            },
            {
                'title': 'Start Date'
            },
            {
                'title': 'Expiry Date'
            },
            {
                'title': 'Licence',
                'searchable': False,
                'orderable': False
            },
            {
                'title': 'Cover Letter',
                'searchable': False,
                'orderable': False
            },
            {
                'title': 'Renewal Letter',
                'searchable': False,
                'orderable': False
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]
        data['licences']['ajax']['url'] = reverse('wl_customer_management:data_licences', args=self.args)

        # global table options
        data['licences']['tableOptions'] = {
            'pageLength': 10
        }

        # returns
        data['returns']['columnDefinitions'] = [
            {
                'title': 'Lodgement Number'
            },
            {
                'title': 'Licence Type'
            },
            {
                'title': 'User'
            },
            {
                'title': 'Lodged On'
            },
            {
                'title': 'Due On'
            },
            {
                'title': 'Status'
            },
            {
                'title': 'Licence',
                'orderable': False
            },
            {
                'title': 'Action',
                'searchable': False,
                'orderable': False
            }
        ]
        data['returns']['ajax']['url'] = reverse('wl_customer_management:data_returns', args=self.args)
        # global table options
        data['returns']['tableOptions'] = {
            'pageLength': 10
        }

        return data

    #########################
    # Applications
    #########################
    @property
    def applications_table_options(self):
        result = super(CustomerLookupView, self).applications_table_options
        result.update({
            'pageLength': 10,
        })
        return result

    @property
    def applications_data_url(self):
        return reverse('wl_customer_management:data_applications', args=self.args)

    @property
    def applications_filters(self):
        # no filters
        return {}

    @property
    def get_applications_session_data(self):
        # no session
        return {}

    #########################
    # Licences
    #########################
    @property
    def licences_table_options(self):
        result = super(CustomerLookupView, self).licences_table_options
        result.update({
            'pageLength': 10,
        })
        return result

    @property
    def licences_data_url(self):
        return reverse('wl_customer_management:data_licences', args=self.args)

    @property
    def licences_filters(self):
        # no filters
        return {}

    @property
    def get_licences_session_data(self):
        # no session
        return {}

    #########################
    # Returns
    #########################
    @property
    def returns_table_options(self):
        result = super(CustomerLookupView, self).returns_table_options
        result.update({
            'pageLength': 10,
        })
        return result

    @property
    def returns_data_url(self):
        return reverse('wl_customer_management:data_returns', args=self.args)

    @property
    def returns_filters(self):
        # no filters
        return {}

    @property
    def get_returns_session_data(self):
        # no session
        return {}

    def get(self, request, *args, **kwargs):
        if 'customer' in self.request.GET:
            customer = get_object_or_404(EmailUser, pk=self.request.GET.get('customer'))

            return redirect('wl_customer_management:customer_lookup', customer.pk)

        context = {}

        if len(self.args) > 0:
            customer = get_object_or_404(EmailUser, pk=self.args[0])

            kwargs['customer'] = customer

            kwargs['log_entry_form'] = CommunicationsLogEntryForm(to=customer.get_full_name(),
                                                                  fromm=self.request.user.get_full_name())

            context = super(CustomerLookupView, self).get_context_data(**kwargs)

        return render(request, self.template_name, context)


class EditDetailsView(OfficerRequiredMixin, TemplateView):
    template_name = 'wl/officer_edit_customer_details.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        customer = get_object_or_404(EmailUser, pk=self.args[0])
        if 'customer' not in kwargs:
            kwargs['customer'] = customer
        if 'form' not in kwargs:
            kwargs['form'] = CustomerDetailsForm(instance=customer)

        # if 'form_id' not in kwargs:
        #     kwargs['form_id'] = IdentificationForm()
        if 'id_url' not in kwargs and bool(customer.identification2):
            #kwargs['id_url'] = customer.identification.file.url
            kwargs['id_url'] = customer.identification2.upload.url

        if 'senior_card_url' not in kwargs and bool(customer.senior_card2):
            #kwargs['senior_card_url'] = customer.senior_card.file.url
            kwargs['senior_card_url'] = customer.senior_card2.upload.url

        return super(EditDetailsView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        customer = get_object_or_404(EmailUser, pk=self.args[0])

        ctx = {
            'customer': customer
        }

        if 'save_details' in request.POST:
            emailuser_form = CustomerDetailsForm(request.POST, instance=customer)
            if emailuser_form.is_valid():
                emailuser_form.save()
                messages.success(request,
                                 'The details were updated. Please note that this may require any licences held by the user to be reissued.')
                return redirect('wl_customer_management:customer_lookup', customer.pk)

            else:
                ctx['form'] = emailuser_form
                return self.get(request, **ctx)

        if 'id' in self.request.FILES:
            #previous_id = customer.identification
            previous_id = customer.identification2
            #customer.identification = Document.objects.create(file=self.request.FILES['id'])
            customer.identification2 = PrivateDocument.objects.create(upload=self.request.FILES['id'])
            customer.save()
            if bool(previous_id):
                previous_id.delete()
            #ctx['id_url'] = customer.identification.file.url
            ctx['id_url'] = customer.identification2.upload.url
            identification_uploaded.send(sender=self.__class__, request=self.request)

        if 'delete_id' in request.POST:
            if bool(customer.identification2):
                customer.identification2.delete()

        if 'senior_card' in self.request.FILES:
            #previous = customer.senior_card
            previous = customer.senior_card2
            #customer.senior_card = Document.objects.create(file=self.request.FILES['senior_card'])
            customer.senior_card2 = PrivateDocument.objects.create(upload=self.request.FILES['senior_card'])
            customer.save()
            if bool(previous):
                previous.delete()
            #ctx['senior_card_url'] = customer.senior_card.file.url
            ctx['senior_card_url'] = customer.senior_card2.upload.url

        if 'delete_senior_card' in request.POST:
            # if bool(customer.senior_card):
            #     customer.senior_card.delete()
            if bool(customer.senior_card2):
                customer.senior_card2.delete()

        return self.get(request, **ctx)


class EditProfileView(OfficerRequiredMixin, TemplateView):
    template_name = 'wl/officer_edit_customer_profile.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        customer = get_object_or_404(EmailUser, pk=self.args[0])

        kwargs['customer'] = customer

        if len(self.args) > 1:
            profile = get_object_or_404(Profile, pk=self.args[1])
            kwargs['profile_form'] = ProfileForm(instance=profile)
            kwargs['address_form'] = AddressForm(instance=profile.postal_address)
        else:
            kwargs['profile_form'] = ProfileForm(user=customer)
            kwargs['address_form'] = AddressForm(user=customer)

        return super(EditProfileView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        customer = get_object_or_404(EmailUser, pk=self.args[0])

        if len(self.args) > 1:
            profile = get_object_or_404(Profile, pk=args[1])
            profile_form = ProfileForm(request.POST, instance=profile)
            address_form = AddressForm(request.POST, instance=profile.postal_address)
        else:
            mutable = request.POST._mutable
            request.POST._mutable = True
            request.POST['user'] = customer.id
            request.POST._mutable = mutable
            profile_form = ProfileForm(request.POST)
            address_form = AddressForm(request.POST)

        if profile_form.is_valid() and address_form.is_valid():
            profile = profile_form.save(commit=False)
            address = address_form.save()
            profile.user = customer
            profile.postal_address = address
            profile.save()
        else:
            return render(request, self.template_name, {'customer': customer,
                                                        'profile_form': profile_form,
                                                        'address_form': address_form})

        messages.success(request, "The profile '%s' was updated." % profile.name)

        return redirect('wl_customer_management:customer_lookup', profile.user.pk)
