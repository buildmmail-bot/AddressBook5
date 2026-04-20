from rest_framework import serializers
from .models import Contact, Admin
import json

class ContactSerializer(serializers.ModelSerializer):
    front_card = serializers.ImageField(required=False, allow_null=True)
    back_card = serializers.ImageField(required=False, allow_null=True)
    phones = serializers.JSONField(required=False)
    emails = serializers.JSONField(required=False)

    class Meta:
        model = Contact
        fields = '__all__'

    def to_internal_value(self, data):
        # Handle both FormData (QueryDict) and JSON (dict)
        try:
            mutable_data = data.copy()  # works for QueryDict (FormData)
        except AttributeError:
            mutable_data = data  # already a plain dict (JSON)

        if 'phones' in mutable_data and isinstance(mutable_data['phones'], str):
            try:
                mutable_data['phones'] = json.loads(mutable_data['phones'])
            except (ValueError, TypeError):
                pass

        if 'emails' in mutable_data and isinstance(mutable_data['emails'], str):
            try:
                mutable_data['emails'] = json.loads(mutable_data['emails'])
            except (ValueError, TypeError):
                pass

        return super().to_internal_value(mutable_data)


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['id', 'name', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}} # Changed to True for security

    def to_representation(self, instance):
        """ This method cleans the data before sending it to React """
        ret = super().to_representation(instance)
        
        # FIX: If email is a list like ['admin1234', 'gmail.com'], join it back with '@'
        if isinstance(ret.get('email'), list):
            ret['email'] = "@".join(ret['email'])
            
        # FIX: If name is a list, join it with a space or take the first element
        if isinstance(ret.get('name'), list):
            ret['name'] = " ".join(ret['name'])
            
        return ret