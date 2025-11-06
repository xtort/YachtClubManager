from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Event, EventCategory, EventActionLog, EventRegistration
from .forms import EventForm, EventContactFormSet
from ManagementApp.mixins import EventEditRequiredMixin, EventDeleteRequiredMixin
from django.shortcuts import redirect, get_object_or_404

ClubUser = get_user_model()


class CalendarView(ListView):
    """Main calendar view displaying all events"""
    model = Event
    template_name = 'CalendarApp/calendar.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        """Get all future events and recent past events"""
        return Event.objects.select_related('category').order_by('start_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = EventCategory.objects.all()
        return context


class EventListView(ListView):
    """List view of all events"""
    model = Event
    template_name = 'CalendarApp/event_list.html'
    context_object_name = 'events'
    paginate_by = 20

    def get_queryset(self):
        return Event.objects.select_related('category').order_by('-start_datetime')


class EventDetailView(DetailView):
    """Detail view for a single event"""
    model = Event
    template_name = 'CalendarApp/event_detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        user = self.request.user
        
        # Check if user can register and if they're already registered
        context['can_register'] = event.can_register(user)
        context['is_registered'] = event.is_registered(user) if user.is_authenticated else False
        context['registration_count'] = event.get_registration_count()
        
        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new event"""
    model = Event
    form_class = EventForm
    template_name = 'CalendarApp/event_form.html'
    success_url = reverse_lazy('calendar:calendar')

    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to create events"""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has create_events permission (editor or admin)
        if not (request.user.has_permission('create_events') or request.user.is_superuser):
            raise PermissionDenied("You don't have permission to create events.")
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['contact_formset'] = EventContactFormSet(self.request.POST)
        else:
            context['contact_formset'] = EventContactFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context['contact_formset']
        
        if contact_formset.is_valid():
            self.object = form.save()
            contact_formset.instance = self.object
            contact_formset.save()
            
            # Log the action
            EventActionLog.objects.create(
                event=self.object,
                user=self.request.user,
                action='created',
                event_title=self.object.title,
                ip_address=self._get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:255]
            )
            
            messages.success(self.request, f'Event "{form.cleaned_data["title"]}" has been created successfully!')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
    def _get_client_ip(self):
        """Get client IP address from request"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class EventUpdateView(EventEditRequiredMixin, UpdateView):
    """View for updating an existing event"""
    model = Event
    form_class = EventForm
    template_name = 'CalendarApp/event_form.html'
    context_object_name = 'event'
    success_url = reverse_lazy('calendar:calendar')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['contact_formset'] = EventContactFormSet(self.request.POST, instance=self.object)
        else:
            context['contact_formset'] = EventContactFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context['contact_formset']
        
        if contact_formset.is_valid():
            form.save()
            contact_formset.save()
            
            # Log the action
            EventActionLog.objects.create(
                event=self.object,
                user=self.request.user,
                action='updated',
                event_title=self.object.title,
                ip_address=self._get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:255]
            )
            
            messages.success(self.request, f'Event "{form.cleaned_data["title"]}" has been updated successfully!')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
    def _get_client_ip(self):
        """Get client IP address from request"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class EventDeleteView(EventDeleteRequiredMixin, DeleteView):
    """View for deleting an event"""
    model = Event
    template_name = 'CalendarApp/event_confirm_delete.html'
    context_object_name = 'event'
    success_url = reverse_lazy('calendar:calendar')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        event_title = self.object.title
        event_data = {
            'title': self.object.title,
            'short_description': self.object.short_description,
            'category': self.object.category.name if self.object.category else None,
            'start_datetime': self.object.start_datetime.isoformat(),
            'end_datetime': self.object.end_datetime.isoformat(),
        }
        
        # Log the action before deletion
        EventActionLog.objects.create(
            event=None,  # Event will be deleted
            user=request.user,
            action='deleted',
            event_title=event_title,
            event_data=event_data,
            ip_address=self._get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
        )
        
        messages.success(request, f'Event "{event_title}" has been deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def _get_client_ip(self):
        """Get client IP address from request"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class EventActionLogView(LoginRequiredMixin, ListView):
    """View for displaying event action logs"""
    model = EventActionLog
    template_name = 'CalendarApp/event_action_log.html'
    context_object_name = 'action_logs'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to view logs (editors and admins)"""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has edit_events or delete_events permission (editor or admin)
        if not (request.user.has_permission('edit_events') or 
                request.user.has_permission('delete_events') or 
                request.user.is_superuser):
            raise PermissionDenied("You don't have permission to view action logs.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return EventActionLog.objects.select_related('user', 'event').order_by('-timestamp')


def calendar_json(request):
    """JSON endpoint for calendar events (for use with calendar libraries like FullCalendar)"""
    events = Event.objects.select_related('category').all()
    events_data = []
    
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_datetime.isoformat(),
            'end': event.end_datetime.isoformat(),
            'description': event.short_description,
            'url': event.get_absolute_url(),
            'color': event.category.color if event.category else '#007bff',
            'category': event.category.name if event.category else 'Uncategorized',
        })
    
    return JsonResponse(events_data, safe=False)


@login_required
@require_http_methods(["GET"])
def member_autocomplete(request):
    """API endpoint for member autocomplete search"""
    from django.db.models import Q
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search by first name, last name, email, or nickname
    members = ClubUser.objects.filter(is_active=True).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(nickname__icontains=query)
    ).order_by('last_name', 'first_name')[:20]
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'text': f"{member.get_full_name()} ({member.email})",
            'name': member.get_full_name(),
            'email': member.email,
        })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["POST"])
def event_register(request, pk):
    """Register a user for an event"""
    event = get_object_or_404(Event, pk=pk)
    user = request.user
    
    # Check if user can register
    if not event.can_register(user):
        messages.error(request, 'You cannot register for this event.')
        return redirect('calendar:event_detail', pk=pk)
    
    # Check if already registered
    if event.is_registered(user):
        messages.info(request, 'You are already registered for this event.')
        return redirect('calendar:event_detail', pk=pk)
    
    # Create registration
    EventRegistration.objects.create(
        event=event,
        member=user
    )
    
    messages.success(request, f'You have successfully registered for "{event.title}"!')
    return redirect('calendar:event_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def event_unregister(request, pk):
    """Unregister a user from an event"""
    event = get_object_or_404(Event, pk=pk)
    user = request.user
    
    # Find the registration
    try:
        registration = EventRegistration.objects.get(event=event, member=user, cancelled=False)
        registration.cancel()
        messages.success(request, f'You have successfully unregistered from "{event.title}".')
    except EventRegistration.DoesNotExist:
        messages.error(request, 'You are not registered for this event.')
    
    return redirect('calendar:event_detail', pk=pk)
