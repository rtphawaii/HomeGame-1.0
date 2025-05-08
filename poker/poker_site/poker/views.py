from django.shortcuts import render
import uuid

try:
    import pokerlib
    print("✅ pokerlib imported")
except ModuleNotFoundError:
    print("❌ still broken")

def index(request):
    user_id = str(uuid.uuid4())  # generate random user ID
    return render(request, 'poker/index.html', {'user_id': user_id})