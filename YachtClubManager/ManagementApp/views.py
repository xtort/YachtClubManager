from django.shortcuts import render
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from CalendarApp.models import EventCategory, Event, EventRegistration, EventRegistrationFee
from .models import Role, MemberType, MemberTypeRelationship
from .forms import EventCategoryForm, ClubUserCreateForm, ClubUserUpdateForm, ProfileUpdateForm, MemberTypeForm, RoleForm, MemberTypeRelationshipForm, EventRegistrationFilterForm
from .mixins import UserManagementRequiredMixin, MemberDirectoryRequiredMixin
from django.db.models import Q
from decimal import Decimal

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
        queryset = ClubUser.objects.select_related('role').order_by('last_name', 'first_name')
        
        # Search functionality
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(nickname__icontains=search_query) |
                Q(primary_phone_number__icontains=search_query) |
                Q(vessel_name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '').strip()
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get relationship data for display
        user = self.get_object()
        context['parent_member'] = user.parent_member
        context['dependent_members'] = user.dependent_members.filter(is_active=True).order_by('relationship_type', 'last_name', 'first_name')
        return context

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


class MembersDirectoryView(MemberDirectoryRequiredMixin, ListView):
    """View for members directory - accessible to members, editors, and admins (but not viewers)"""
    model = ClubUser
    template_name = 'ManagementApp/members_directory.html'
    context_object_name = 'members'
    paginate_by = 30

    def get_queryset(self):
        # Only show active members
        queryset = ClubUser.objects.filter(is_active=True).select_related('role').order_by('last_name', 'first_name')
        
        # Search functionality
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(nickname__icontains=search_query) |
                Q(primary_phone_number__icontains=search_query) |
                Q(vessel_name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '').strip()
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get relationship data for display
        user = self.get_object()
        context['parent_member'] = user.parent_member
        context['dependent_members'] = user.dependent_members.filter(is_active=True).order_by('relationship_type', 'last_name', 'first_name')
        return context

    def get_form_kwargs(self):
        """Add request to form kwargs for file upload handling"""
        kwargs = super().get_form_kwargs()
        # Ensure instance is set (should already be set by UpdateView, but being explicit)
        if 'instance' not in kwargs:
            kwargs['instance'] = self.get_object()
        # Only add files if this is a POST request (Django handles this automatically, but being explicit)
        if self.request.method == 'POST':
            kwargs['files'] = self.request.FILES
        return kwargs

    def form_valid(self, form):
        password_changed = bool(form.cleaned_data.get('password1'))
        messages.success(
            self.request,
            'Your profile has been updated successfully!'
            + (' Password has been changed.' if password_changed else '')
        )
        return super().form_valid(form)


# Member Type Management Views
class MemberTypeListView(UserManagementRequiredMixin, ListView):
    """List view of all member types"""
    model = MemberType
    template_name = 'ManagementApp/member_type_list.html'
    context_object_name = 'member_types'

    def get_queryset(self):
        return MemberType.objects.all().order_by('display_order', 'name')


class MemberTypeCreateView(UserManagementRequiredMixin, CreateView):
    """View for creating a new member type"""
    model = MemberType
    form_class = MemberTypeForm
    template_name = 'ManagementApp/member_type_form.html'
    success_url = reverse_lazy('management:member_type_list')

    def form_valid(self, form):
        # Count existing rows in the MemberType table
        existing_count = MemberType.objects.count()
        # Set display order to (count - 1)
        form.instance.display_order = max(existing_count, 0)
        # Add success message
        messages.success(
            self.request,
            f'Member Type "{form.cleaned_data["name"]}" has been created successfully!'
        )
        return super().form_valid(form)


class MemberTypeUpdateView(UserManagementRequiredMixin, UpdateView):
    """View for updating an existing member type"""
    model = MemberType
    form_class = MemberTypeForm
    template_name = 'ManagementApp/member_type_form.html'
    success_url = reverse_lazy('management:member_type_list')
    context_object_name = 'member_type'

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Member Type "{form.cleaned_data["name"]}" has been updated successfully!'
        )
        return super().form_valid(form)


class MemberTypeDeleteView(UserManagementRequiredMixin, DeleteView):
    """View for deleting a member type"""
    model = MemberType
    template_name = 'ManagementApp/member_type_confirm_delete.html'
    success_url = reverse_lazy('management:member_type_list')
    context_object_name = 'member_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if any users are using this member type
        context['member_count'] = self.object.members.count()
        return context

    def form_valid(self, form):
        member_type_name = self.object.name
        member_count = self.object.members.count()
        
        if member_count > 0:
            messages.warning(
                self.request,
                f'Member Type "{member_type_name}" deleted. {member_count} member(s) using this type will have it removed.'
            )
        else:
            messages.success(
                self.request,
                f'Member Type "{member_type_name}" has been deleted successfully!'
            )
        return super().form_valid(form)


# Role Management Views
class RoleListView(UserManagementRequiredMixin, ListView):
    """List view of all roles"""
    model = Role
    template_name = 'ManagementApp/role_list.html'
    context_object_name = 'roles'

    def get_queryset(self):
        return Role.objects.all().order_by('name')


class RoleCreateView(UserManagementRequiredMixin, CreateView):
    """View for creating a new role"""
    model = Role
    form_class = RoleForm
    template_name = 'ManagementApp/role_form.html'
    success_url = reverse_lazy('management:role_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Role "{form.cleaned_data["name"]}" has been created successfully!'
        )
        return super().form_valid(form)


class RoleUpdateView(UserManagementRequiredMixin, UpdateView):
    """View for updating an existing role"""
    model = Role
    form_class = RoleForm
    template_name = 'ManagementApp/role_form.html'
    success_url = reverse_lazy('management:role_list')
    context_object_name = 'role'

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Role "{form.cleaned_data["name"]}" has been updated successfully!'
        )
        return super().form_valid(form)


class RoleDeleteView(UserManagementRequiredMixin, DeleteView):
    """View for deleting a role"""
    model = Role
    template_name = 'ManagementApp/role_confirm_delete.html'
    success_url = reverse_lazy('management:role_list')
    context_object_name = 'role'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if any users are using this role
        context['user_count'] = self.object.users.count()
        return context

    def form_valid(self, form):
        role_name = self.object.get_name_display()
        user_count = self.object.users.count()
        
        if user_count > 0:
            messages.warning(
                self.request,
                f'Role "{role_name}" deleted. {user_count} user(s) using this role will have it set to NULL.'
            )
        else:
            messages.success(
                self.request,
                f'Role "{role_name}" has been deleted successfully!'
            )
        return super().form_valid(form)


# Member Type Relationship Management Views
class MemberTypeRelationshipListView(UserManagementRequiredMixin, ListView):
    """List view of all member type relationships"""
    model = MemberTypeRelationship
    template_name = 'ManagementApp/member_type_relationship_list.html'
    context_object_name = 'relationships'

    def get_queryset(self):
        return MemberTypeRelationship.objects.select_related('parent_type', 'child_type').all().order_by('parent_type__display_order', 'child_type__display_order')


class MemberTypeRelationshipCreateView(UserManagementRequiredMixin, CreateView):
    """View for creating a new member type relationship"""
    model = MemberTypeRelationship
    form_class = MemberTypeRelationshipForm
    template_name = 'ManagementApp/member_type_relationship_form.html'
    success_url = reverse_lazy('management:member_type_relationship_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if member types are configured for parent/child relationships
        context['has_parent_types'] = MemberType.objects.filter(can_be_parent=True, is_active=True).exists()
        context['has_child_types'] = MemberType.objects.filter(can_be_child=True, is_active=True).exists()
        context['has_active_types'] = MemberType.objects.filter(is_active=True).exists()
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Relationship "{form.cleaned_data["parent_type"].name} → {form.cleaned_data["child_type"].name}" has been created successfully!'
        )
        return super().form_valid(form)


class MemberTypeRelationshipUpdateView(UserManagementRequiredMixin, UpdateView):
    """View for updating an existing member type relationship"""
    model = MemberTypeRelationship
    form_class = MemberTypeRelationshipForm
    template_name = 'ManagementApp/member_type_relationship_form.html'
    success_url = reverse_lazy('management:member_type_relationship_list')
    context_object_name = 'relationship'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if member types are configured for parent/child relationships
        context['has_parent_types'] = MemberType.objects.filter(can_be_parent=True, is_active=True).exists()
        context['has_child_types'] = MemberType.objects.filter(can_be_child=True, is_active=True).exists()
        context['has_active_types'] = MemberType.objects.filter(is_active=True).exists()
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Relationship "{form.cleaned_data["parent_type"].name} → {form.cleaned_data["child_type"].name}" has been updated successfully!'
        )
        return super().form_valid(form)


class MemberTypeRelationshipDeleteView(UserManagementRequiredMixin, DeleteView):
    """View for deleting a member type relationship"""
    model = MemberTypeRelationship
    template_name = 'ManagementApp/member_type_relationship_confirm_delete.html'
    success_url = reverse_lazy('management:member_type_relationship_list')
    context_object_name = 'relationship'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if any users are using this relationship
        parent_type = self.object.parent_type
        child_type = self.object.child_type
        context['user_count'] = ClubUser.objects.filter(
            parent_member__member_types=parent_type,
            member_types=child_type
        ).count()
        return context

    def form_valid(self, form):
        relationship_name = str(self.object)
        user_count = ClubUser.objects.filter(
            parent_member__member_types=self.object.parent_type,
            member_types=self.object.child_type
        ).count()
        
        if user_count > 0:
            messages.warning(
                self.request,
                f'Relationship "{relationship_name}" deleted. {user_count} member(s) using this relationship will remain but the relationship type will no longer be enforced.'
            )
        else:
            messages.success(
                self.request,
                f'Relationship "{relationship_name}" has been deleted successfully!'
            )
        return super().form_valid(form)


@login_required
@require_http_methods(["POST"])
def member_type_reorder(request):
    """AJAX endpoint to reorder member types"""
    if not (request.user.has_permission('manage_users') or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        order = data.get('order', [])
        
        if not order:
            return JsonResponse({'success': False, 'error': 'No order provided'})
        
        # Update display_order for each member type based on its position in the order
        for index, member_type_id in enumerate(order):
            try:
                member_type = MemberType.objects.get(pk=member_type_id)
                member_type.display_order = index
                member_type.save(update_fields=['display_order'])
            except MemberType.DoesNotExist:
                continue
        
        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def registrations_report(request):
    """Generate a registrations report with filtering options"""
    # Check permissions - only Admins and Editors can access
    if not (request.user.has_permission('edit_events') or request.user.has_permission('manage_users') or request.user.is_superuser):
        raise PermissionDenied("You don't have permission to access this report.")
    
    filter_form = EventRegistrationFilterForm(request.GET)
    registrations_data = []
    total_revenue = Decimal('0.00')
    
    if filter_form.is_valid():
        # Start with all non-cancelled registrations
        registrations = EventRegistration.objects.filter(cancelled=False).select_related(
            'event', 'member'
        ).prefetch_related('member__member_types', 'additional_members')
        
        # Filter by event title
        event_title = filter_form.cleaned_data.get('event_title')
        if event_title:
            registrations = registrations.filter(event__title__icontains=event_title)
        
        # Filter by start date (events starting on or after this date)
        start_date = filter_form.cleaned_data.get('start_date')
        if start_date:
            registrations = registrations.filter(event__start_datetime__date__gte=start_date)
        
        # Filter by end date (events ending on or before this date)
        end_date = filter_form.cleaned_data.get('end_date')
        if end_date:
            registrations = registrations.filter(event__end_datetime__date__lte=end_date)
        
        # Build report data
        for registration in registrations:
            # Primary member
            member = registration.member
            member_types = ', '.join([mt.name for mt in member.member_types.filter(is_active=True)])
            
            # Calculate fee for primary member based on their member type
            primary_fee = Decimal('0.00')
            member_type_list = member.member_types.filter(is_active=True)
            for member_type in member_type_list:
                try:
                    fee = EventRegistrationFee.objects.get(event=registration.event, member_type=member_type)
                    primary_fee = fee.fee_amount
                    break  # Use first matching fee
                except EventRegistrationFee.DoesNotExist:
                    pass
            
            # Format address
            address_parts = []
            if member.address1:
                address_parts.append(member.address1)
            if member.address2:
                address_parts.append(member.address2)
            if member.city:
                address_parts.append(member.city)
            if member.state:
                address_parts.append(member.get_state_display())
            if member.zip_code:
                address_parts.append(member.zip_code)
            full_address = ', '.join(address_parts) if address_parts else 'N/A'
            
            registrations_data.append({
                'event_title': registration.event.title,
                'event_start': registration.event.start_datetime,
                'event_end': registration.event.end_datetime,
                'full_name': member.get_full_name(),
                'address': full_address,
                'email': member.email,
                'phone': member.primary_phone_number or 'N/A',
                'member_type': member_types or 'N/A',
                'registration_date': registration.registered_at,
                'registration_fee': primary_fee,
                'is_primary': True,
            })
            
            total_revenue += primary_fee
            
            # Additional members (dependents)
            for additional_member in registration.additional_members.all():
                additional_member_types = ', '.join([mt.name for mt in additional_member.member_types.filter(is_active=True)])
                
                # Calculate fee for additional member based on their member type
                additional_fee = Decimal('0.00')
                additional_member_type_list = additional_member.member_types.filter(is_active=True)
                for member_type in additional_member_type_list:
                    try:
                        fee = EventRegistrationFee.objects.get(event=registration.event, member_type=member_type)
                        additional_fee = fee.fee_amount
                        break  # Use first matching fee
                    except EventRegistrationFee.DoesNotExist:
                        pass
                
                # Format address for additional member
                additional_address_parts = []
                if additional_member.address1:
                    additional_address_parts.append(additional_member.address1)
                if additional_member.address2:
                    additional_address_parts.append(additional_member.address2)
                if additional_member.city:
                    additional_address_parts.append(additional_member.city)
                if additional_member.state:
                    additional_address_parts.append(additional_member.get_state_display())
                if additional_member.zip_code:
                    additional_address_parts.append(additional_member.zip_code)
                additional_full_address = ', '.join(additional_address_parts) if additional_address_parts else 'N/A'
                
                registrations_data.append({
                    'event_title': registration.event.title,
                    'event_start': registration.event.start_datetime,
                    'event_end': registration.event.end_datetime,
                    'full_name': additional_member.get_full_name(),
                    'address': additional_full_address,
                    'email': additional_member.email,
                    'phone': additional_member.primary_phone_number or 'N/A',
                    'member_type': additional_member_types or 'N/A',
                    'registration_date': registration.registered_at,
                    'registration_fee': additional_fee,
                    'is_primary': False,
                })
                
                total_revenue += additional_fee
        
        # Sort by event start date, then by registration date
        registrations_data.sort(key=lambda x: (x['event_start'], x['registration_date']))
    
    context = {
        'filter_form': filter_form,
        'registrations_data': registrations_data,
        'total_revenue': total_revenue,
        'has_results': len(registrations_data) > 0,
    }
    
    return render(request, 'ManagementApp/registrations_report.html', context)
