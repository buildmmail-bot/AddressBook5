from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Contact
import json
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from rest_framework import status
from django.db.models import Q

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Admin
from .serializers import ContactSerializer, AdminSerializer

# ===================== CONTACT LIST =====================

@csrf_exempt
def contact_list(request):
    if request.method == "GET":
        contacts = Contact.objects.all()
        data = []
        for c in contacts:
            data.append({
                "id": c.id,
                "name": c.name,
                "company_name": c.company_name,
                "address": c.address,
                "phones": c.phones,
                "emails": c.emails,
                "front_card": c.front_card.url if c.front_card else None,
                "back_card": c.back_card.url if c.back_card else None,
                "github": getattr(c, 'github', ""),
                "linkedin": getattr(c, 'linkedin', ""),
                "website": getattr(c, 'website', ""),
                "qr_code": c.qr_code.url if c.qr_code else None,
            })
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        if request.content_type and 'multipart' in request.content_type:
            name = request.POST.get("name")
            company_name = request.POST.get("company_name")
            address = request.POST.get("address", "")

            phones_raw = request.POST.get("phones")
            if phones_raw:
                phones_val = json.loads(phones_raw)
            else:
                p = request.POST.get("phone")
                phones_val = [p] if p else []

            emails_raw = request.POST.get("emails", "[]")
            try:
                emails = json.loads(emails_raw)
            except Exception:
                emails = request.POST.getlist("emails[]")

            front_card = request.FILES.get("front_card")
            back_card = request.FILES.get("back_card")
            qr_code = request.FILES.get("qr_code")

        else:
            data = json.loads(request.body)
            name = data.get("name")
            company_name = data.get("company_name")
            address = data.get("address", "")
            emails = data.get("emails", [])
            phones_val = data.get("phones", [])
            front_card = None
            back_card = None
            qr_code = None

        contact = Contact.objects.create(
            name=name,
            company_name=company_name,
            address=address,
            phones=phones_val,
            emails=emails,
            front_card=front_card,
            back_card=back_card,
            qr_code=qr_code,
        )

        return JsonResponse({
            "message": "Saved",
            "id": contact.id,
            "name": contact.name,
            "company_name": contact.company_name,
            "address": contact.address,
            "phones": contact.phones,
            "emails": contact.emails,
            "front_card": contact.front_card.url if contact.front_card else None,
            "back_card": contact.back_card.url if contact.back_card else None,
            "qr_code": contact.qr_code.url if contact.qr_code else None,
})


# ===================== CONTACT DETAIL =====================

@csrf_exempt
def contact_detail(request, id):
    try:
        contact = Contact.objects.get(id=id)
    except Contact.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method == "DELETE":
        contact.delete()
        return JsonResponse({"message": "Deleted"})

    elif request.method == "PUT":
        try:
            data = json.loads(request.body.decode('utf-8'))

            contact.name = data.get("name", contact.name)
            contact.company_name = data.get("company_name", contact.company_name)
            contact.address = data.get("address", contact.address)
            contact.emails = data.get("emails", contact.emails)
            contact.phones = data.get("phones", contact.phones)

            contact.save()

            return JsonResponse({
                "id": contact.id,
                "name": contact.name,
                "company_name": contact.company_name,
                "address": contact.address,
                "phones": contact.phones,
                "emails": contact.emails,
                "front_card": contact.front_card.url if contact.front_card else None,
                "back_card": contact.back_card.url if contact.back_card else None,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# ===================== CLEAR CARD =====================

@csrf_exempt
def clear_card(request, id):
    if request.method == "POST":
        try:
            contact = Contact.objects.get(id=id)
            data = json.loads(request.body)
            field = data.get("field")
            if field == "front_card":
                if contact.front_card:
                    contact.front_card.delete(save=False)
                contact.front_card = None
            elif field == "back_card":
                if contact.back_card:
                    contact.back_card.delete(save=False)
                contact.back_card = None
            contact.save()
            return JsonResponse({"message": "Card deleted"})
        except Contact.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid method"}, status=405)


# ===================== LOGIN =====================

# ===================== LOGIN (FIXED) =====================
# ===================== LOGIN (FIXED INDENTATION) =====================
@csrf_exempt
def login_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body or "{}")
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return JsonResponse({"error": "Email and password required"}, status=400)

            # 1. Look for user, if not found, CREATE them
            user_obj = User.objects.filter(email=email).first()
            if not user_obj:
                user_obj = User.objects.create_user(username=email, email=email, password=password)
            
            # 2. Authenticate
            auth_user = authenticate(username=user_obj.username, password=password)

            if auth_user is not None:
                login(request, auth_user)

                # FIX: Get name as string, not a list
                full_email = str(auth_user.email)
                display_name = full_email.split('@') [0]

                # 3. Sync with Admin List
                Admin.objects.get_or_create(
                    email=full_email,
                    defaults={
                        "name": display_name,
                        "password": "" 
                    }
                )

                return JsonResponse({
                    "name": auth_user.username,
                    "email": auth_user.email
                })
            else:
                # This 'else' must align perfectly with 'if auth_user is not None'
                return JsonResponse({"error": "Invalid password"}, status=401)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Login active"})
              
        


      

# ===================== PASSWORD RESET (FIXED) =====================

@csrf_exempt
def password_reset(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            # Added a default None to prevent crash if key is missing
            new_password = data.get("new_password", None) 

            if not email:
                return JsonResponse({"error": "Email required"}, status=400)

            # Check if user exists first
            if not User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Admin with this email not found"}, status=404)
            
            # If your React app is just 'checking' if email exists:
            if new_password is None:
                return JsonResponse({"message": "Email verified. Please provide new password."})

            # Logic to actually update password
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            return JsonResponse({"message": "Password updated successfully"})
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)

# ===================== REGISTER =====================

@csrf_exempt
def register_admin(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        name = data.get("name", email)

        if not email or not password:
            return JsonResponse({"error": "Email and password required"}, status=400)

        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "Admin already exists"}, status=400)

        User.objects.create_user(username=email, email=email, password=password)

        Admin.objects.get_or_create(
            email=email,
            defaults={"name": name, "password": password}
        )

        return JsonResponse({"message": "Admin added successfully"})

    return JsonResponse({"message": "Register endpoint active"})


@api_view(['GET', 'POST'])
def admin_list(request):
    if request.method == 'GET':
        search = request.query_params.get('search', '')
        admins = Admin.objects.filter(
            Q(name__icontains=search) | Q(email__icontains=search)
        ).order_by('-id')
        serializer = AdminSerializer(admins, many=True)
        return Response({'count': admins.count(), 'results': serializer.data})

    if request.method == 'POST':
        serializer = AdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def admin_detail(request, pk):
    try:
        admin = Admin.objects.get(pk=pk)
    except Admin.DoesNotExist:
        return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AdminSerializer(admin)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = AdminSerializer(admin, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        admin.delete()
        return Response({'message': 'Admin deleted'}, status=status.HTTP_204_NO_CONTENT)


# ===================== PASSWORD RESET =====================

@csrf_exempt
def password_reset(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        new_password = data.get("new_password")

        try:
            admin = Admin.objects.get(email=email)
            admin.password = new_password
            admin.save()
            return JsonResponse({"message": "Password updated successfully"})
        except Admin.DoesNotExist:
            return JsonResponse({"error": "Admin with this email not found"}, status=404)

    return JsonResponse({"error": "Invalid method"}, status=405)