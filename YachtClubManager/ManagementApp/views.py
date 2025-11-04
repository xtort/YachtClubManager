from django.shortcuts import render
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from CalendarApp.models import EventCategory, Event
from .forms import EventCategoryForm, ClubUserCreateForm, ClubUserUpdateForm, ProfileUpdateForm
from .mixins import UserManagementRequiredMixin

ClubUser = get_user_model()


class EventCategoryListView(LoginRequiredMixin, ListView):
    """List view of all event categories"""
    model = EventCategory
    template_name = 'ManagementApp/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return EventCategory.objects.all().order_by('name')


class EventCategoryCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new event category"""
    model = EventCategory
    form_class = EventCategoryForm
    template_name = 'ManagementApp/category_form.html'
    success_url = reverse_lazy('management:category_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Category "{form.cleaned_data["name"]}" has been created successfully!'
        )
        return super().form_valid(form)


class EventCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating an existing event category"""
    model = EventCategory
    form_class = EventCategoryForm
    template_name = 'ManagementApp/category_form.html'
    success_url = reverse_lazy('management:category_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Category "{form.cleaned_data["name"]}" has been updated successfully!'
        )
        return super().form_valid(form)


class EventCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting an event category"""
    model = EventCategory
    template_name = 'ManagementApp/category_confirm_delete.html'
    success_url = reverse_lazy('management:category_list')
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if any events are using this category
        context['event_count'] = Event.objects.filter(category=self.object).count()
        return context

    def form_valid(self, form):
        category_name = self.object.name
        event_count = Event.objects.filter(category=self.object).count()
        
        if event_count > 0:
            # If events use this category, they'll be set to NULL
            messages.warning(
                self.request,
                f'Category "{category_name}" deleted. {event_count} event(s) using this category have been set to "Uncategorized".'
            )
        else:
            messages.success(
                self.request,
                f'Category "{category_name}" has been deleted successfully!'
            )
        return super().form_valid(form)


def management_dashboard(request):
    """Main dashboard for management functions"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    categories = EventCategory.objects.all()
    events = Event.objects.all()
    users = ClubUser.objects.all()
    
    # Count action logs if user has permission
    total_action_logs = 0
    if request.user.has_permission('edit_events') or request.user.has_permission('delete_events') or request.user.is_superuser:
        from CalendarApp.models import EventActionLog
        total_action_logs = EventActionLog.objects.count()
    
    context = {
        'total_categories': categories.count(),
        'total_events': events.count(),
        'total_users': users.count(),
        'total_action_logs': total_action_logs,
        'recent_events': events.order_by('-created_at')[:5],
    }
    
    return render(request, 'ManagementApp/dashboard.html', context)


def dashboard_section(request):
    """View for displaying different dashboard sections"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    section = request.GET.get('section', 'overview')
    
    context = {
        'section': section,
    }
    
    # Add section-specific context
    if section == 'events':
        categories = EventCategory.objects.all()
        events = Event.objects.all()
        
        total_action_logs = 0
        if request.user.has_permission('edit_events') or request.user.has_permission('delete_events') or request.user.is_superuser:
            from CalendarApp.models import EventActionLog
            total_action_logs = EventActionLog.objects.count()
        
        context.update({
            'total_categories': categories.count(),
            'total_events': events.count(),
            'total_action_logs': total_action_logs,
            'recent_events': events.order_by('-created_at')[:5],
        })
    elif section == 'users':
        if request.user.is_superuser or request.user.has_permission('manage_users'):
            users = ClubUser.objects.all()
            context.update({
                'total_users': users.count(),
            })
        else:
            raise PermissionDenied("You don't have permission to view this section.")
    
    template_name = f'ManagementApp/sections/{section}.html'
    return render(request, template_name, context)


# User Management Views
class ClubUserListView(UserManagementRequiredMixin, ListView):
    """List view of all club users"""
    model = ClubUser
    template_name = 'ManagementApp/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        return ClubUser.objects.select_related('role').order_by('last_name', 'first_name')


class ClubUserCreateView(UserManagementRequiredMixin, CreateView):
    """View for creating a new club user"""
    model = ClubUser
    form_class = ClubUserCreateForm
    template_name = 'ManagementApp/user_form.html'
    success_url = reverse_lazy('management:user_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'User "{form.cleaned_data["email"]}" has been created successfully!'
        )
        return super().form_valid(form)


class ClubUserUpdateView(UserManagementRequiredMixin, UpdateView):
    """View for updating an existing club user"""
    model = ClubUser
    form_class = ClubUserUpdateForm
    template_name = 'ManagementApp/user_form.html'
    success_url = reverse_lazy('management:user_list')
    context_object_name = 'user'

    def form_valid(self, form):
        password_changed = bool(form.cleaned_data.get('password1'))
        messages.success(
            self.request,
            f'User "{form.cleaned_data["email"]}" has been updated successfully!'
            + (' Password has been changed.' if password_changed else '')
        )
        return super().form_valid(form)


class ClubUserDeleteView(UserManagementRequiredMixin, DeleteView):
    """View for deleting a club user"""
    model = ClubUser
    template_name = 'ManagementApp/user_confirm_delete.html'
    success_url = reverse_lazy('management:user_list')
    context_object_name = 'user'

    def form_valid(self, form):
        user_email = self.object.email
        messages.success(
            self.request,
            f'User "{user_email}" has been deleted successfully!'
        )
        return super().form_valid(form)


# Profile Management Views (for users to manage their own profiles)
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for users to update their own profile"""
    model = ClubUser
    form_class = ProfileUpdateForm
    template_name = 'ManagementApp/profile_form.html'
    success_url = reverse_lazy('calendar:calendar')
    context_object_name = 'user'

    def get_object(self):
        """Return the current user"""
        return self.request.user

    def get_form_kwargs(self):
        """Add request to form kwargs for file upload handling"""
        kwargs = super().get_form_kwargs()
        kwargs.update({'files': self.request.FILES})
        return kwargs

    def form_valid(self, form):
        password_changed = bool(form.cleaned_data.get('password1'))
        messages.success(
            self.request,
            'Your profile has been updated successfully!'
            + (' Password has been changed.' if password_changed else '')
        )
        return super().form_valid(form)
