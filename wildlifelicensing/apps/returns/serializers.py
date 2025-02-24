from rest_framework import serializers

from wildlifelicensing.apps.returns.models import Return, ReturnAmendmentRequest


class ReturnSerializer(serializers.Serializer):
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = Return
        exclude = ("application", "applicationrequest_ptr", "licence")


class ReturnAmendmentRequestSerializer(serializers.Serializer):
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = ReturnAmendmentRequest
        fields = ("status", "reason")


class ReturnLogEntrySerializer(serializers.Serializer):
    type = serializers.CharField(source="get_type_display")
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Return
        exclude = ("ret", "communicationslogentry_ptr", "customer", "officer")

    def get_documents(self, obj):
        return [(str(document), document.file.url) for document in obj.documents.all()]
