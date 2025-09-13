from django.shortcuts import render, redirect, get_object_or_404
from .models import Item
from .forms import ItemForm

def item_list(request):
    items = Item.objects.all()  # Python ORM only
    return render(request, 'hello/item_list.html', {'items': items})

def home(request):
    return render(request, 'hello/home.html')

def add_item_view(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)  # include request.FILES for images
        if form.is_valid():
            form.save()
            return redirect('add_item')
    else:
        form = ItemForm()

    items = Item.objects.all()
    return render(request, 'hello/add_item.html', {'form': form, 'items': items})


def delete_item_post(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        if item_id:
            item = get_object_or_404(Item, id=item_id)
            item.delete()
    return redirect('add_item')

