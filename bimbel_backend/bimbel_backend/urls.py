from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/admin/', include('admin_panel.urls')),
    path('api/tutor/', include('tutor_panel.urls')),
    path("api/student/", include("student_panel.urls")),

]

# Tambahkan ini untuk serve file media (upload)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
