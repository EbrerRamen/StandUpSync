from django.shortcuts import render, redirect, get_object_or_404
from .models import Team, Membership, StandUpEntry
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from datetime import date, datetime
from .forms import CustomUserCreationForm, TeamForm, StandupForm
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q, Count
from threading import current_thread
import logging
from django.views.decorators.http import require_POST
from .utils import summarize_text

logger = logging.getLogger(__name__)

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_thread().request = request
        response = self.get_response(request)
        if hasattr(current_thread(), 'request'):
            del current_thread().request
        return response

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect('home')
            except Exception as e:
                logger.error(f"Error during user registration: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def home(request):
    # Get user's teams with related data
    user_teams = Team.objects.filter(
        membership__user=request.user
    ).select_related('creator').prefetch_related(
        'membership_set__user'
    ).annotate(
        member_count=Count('membership')
    )
    
    # Get today's entries
    today_entries = StandUpEntry.objects.filter(
        team__in=user_teams,
        date=date.today()
    ).select_related('team', 'user')
    
    # Get recent entries
    recent_entries = StandUpEntry.objects.filter(
        team__in=user_teams
    ).select_related('team', 'user').order_by('-date', '-created_at')[:5]
    
    return render(request, 'core/home.html', {
        'entries': today_entries,
        'teams': user_teams,
        'recent_entries': recent_entries,
        'user': request.user
    })

@login_required
def team_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        team = Team.objects.create(name=name, creator=request.user)
        Membership.objects.create(user=request.user, team=team, role='lead')
        messages.success(request, f'Team "{name}" created successfully!')
        return redirect('home')
    return render(request, 'core/team_create.html')

@login_required
def team_join(request):
    if request.method == 'POST':
        code = request.POST.get('invite_code')
        try:
            team = Team.objects.get(invite_code=code)
            membership, created = Membership.objects.get_or_create(
                user=request.user, 
                team=team,
                defaults={'role': 'member'}
            )
            if created:
                messages.success(request, f'Successfully joined team "{team.name}"!')
            else:
                messages.info(request, f'You are already a member of team "{team.name}"')
            return redirect('home')
        except Team.DoesNotExist:
            messages.error(request, 'Invalid invite code')
            return render(request, 'core/team_join.html', {'error': 'Invalid code'})
    return render(request, 'core/team_join.html')

@login_required
def team_leave(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    membership = get_object_or_404(Membership, user=request.user, team=team)
    
    if team.is_creator(request.user):
        messages.error(request, 'Team creators cannot leave their team. Transfer ownership or delete the team instead.')
        return redirect('home')
    
    membership.delete()
    messages.success(request, f'Successfully left team "{team.name}"')
    return redirect('home')

@login_required
def team_delete(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    if not team.is_creator(request.user):
        return HttpResponseForbidden("Only team creators can delete teams")
    
    team_name = team.name
    team.delete()
    messages.success(request, f'Team "{team_name}" has been deleted')
    return redirect('home')

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    membership = get_object_or_404(Membership, user=request.user, team=team)
    members = Membership.objects.filter(team=team).select_related('user')
    
    context = {
        'team': team,
        'members': members,
        'is_creator': team.is_creator(request.user),
        'user_role': membership.role,
    }
    return render(request, 'core/team_detail.html', context)

@login_required
def team_edit(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    if not team.is_creator(request.user):
        return HttpResponseForbidden("Only team creators can edit teams")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if not name:
            messages.error(request, 'Team name is required')
            return render(request, 'core/team_edit.html', {'team': team})
        
        team.name = name
        team.save()
        messages.success(request, f'Team "{name}" updated successfully!')
        return redirect('team_detail', team_id=team.id)
    
    return render(request, 'core/team_edit.html', {'team': team})

@login_required
def team_change_role(request, team_id, membership_id):
    team = get_object_or_404(Team, id=team_id)
    membership = get_object_or_404(Membership, id=membership_id, team=team)
    
    # Only team leads can change roles
    if not team.is_creator(request.user):
        return HttpResponseForbidden("Only team leads can change roles")
    
    # Cannot change the role of the team creator
    if membership.user == team.creator:
        return HttpResponseForbidden("Cannot change the role of the team creator")
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in dict(Membership.ROLE_CHOICES):
            membership.role = new_role
            membership.save()
            messages.success(request, f'Successfully updated {membership.user.username}\'s role to {membership.get_role_display()}')
        else:
            messages.error(request, 'Invalid role selected')
    
    return redirect('team_detail', team_id=team.id)

@login_required
def team_remove_member(request, team_id, membership_id):
    team = get_object_or_404(Team, id=team_id)
    
    # Only team leads can remove members
    if not team.is_creator(request.user):
        return HttpResponseForbidden("Only team leads can remove members")
    
    if request.method == 'POST':
        # Handle bulk removal
        if 'membership_ids' in request.POST:
            membership_ids = request.POST.get('membership_ids').split(',')
            memberships = Membership.objects.filter(
                id__in=membership_ids,
                team=team
            ).exclude(user=team.creator)  # Cannot remove team creator
            
            if memberships.exists():
                usernames = [m.user.username for m in memberships]
                memberships.delete()
                messages.success(request, f'Successfully removed {len(usernames)} members from the team')
            return redirect('team_detail', team_id=team.id)
        
        # Handle single member removal
        membership = get_object_or_404(Membership, id=membership_id, team=team)
        
        # Cannot remove the team creator
        if membership.user == team.creator:
            return HttpResponseForbidden("Cannot remove the team creator")
        
        username = membership.user.username
        membership.delete()
        messages.success(request, f'Successfully removed {username} from the team')
        return redirect('team_detail', team_id=team.id)
    
    return render(request, 'core/team_remove_member.html', {
        'team': team,
        'member': membership
    })

@login_required
def standup_list(request):
    # Get user's teams
    teams = Team.objects.filter(membership__user=request.user)
    selected_team = request.GET.get('team')
    selected_status = request.GET.get('status')
    
    # Get entries for user's teams
    entries = StandUpEntry.objects.filter(team__in=teams)
    
    # Apply filters
    if selected_team:
        entries = entries.filter(team_id=selected_team)
    if selected_status:
        entries = entries.filter(status=selected_status)
    
    # Order by date and time
    entries = entries.order_by('-date', '-created_at')
    
    # Debug logging
    logger.info(f"Found {entries.count()} entries")
    for entry in entries:
        logger.info(f"Entry ID: {entry.id}")
        logger.info(f"Team: {entry.team.name}")
        logger.info(f"User: {entry.user.username}")
        logger.info(f"Date: {entry.date}")
    
    context = {
        'entries': entries,
        'teams': teams,
        'selected_team': selected_team,
        'selected_status': selected_status,
    }
    return render(request, 'core/standup_list.html', context)

@login_required
def standup_create(request):
    if request.method == 'POST':
        yesterday = request.POST.get('yesterday')
        today = request.POST.get('today')
        blockers = request.POST.get('blockers')
        team_id = request.POST.get('team')
        
        if not all([yesterday, today, team_id]):
            messages.error(request, 'All fields are required')
            return render(request, 'core/standup_create.html', {
                'yesterday': yesterday,
                'today': today,
                'blockers': blockers,
                'teams': Team.objects.filter(membership__user=request.user)
            })
        
        team = get_object_or_404(Team, id=team_id)
        if not Membership.objects.filter(user=request.user, team=team).exists():
            return HttpResponseForbidden("You are not a member of this team")
        
        # Generate summaries
        yesterday_summary = None
        today_summary = None
        blockers_summary = None
        
        # Create the standup entry
        standup = StandUpEntry.objects.create(
            user=request.user,
            team=team,
            yesterday=yesterday,
            today=today,
            blockers=blockers,
            yesterday_summary=yesterday_summary,
            today_summary=today_summary,
            blockers_summary=blockers_summary
        )
        
        # Debug logging
        logger.info(f"Created standup entry {standup.id}")
        
        messages.success(request, 'Stand-up entry created successfully!')
        return redirect('standup_list')
    
    # Get user's teams for the dropdown
    teams = Team.objects.filter(membership__user=request.user)
    if not teams.exists():
        messages.warning(request, 'You need to join a team before creating a stand-up entry.')
        return redirect('team_join')
    
    return render(request, 'core/standup_create.html', {'teams': teams})

@login_required
def standup_edit(request, entry_id):
    entry = get_object_or_404(StandUpEntry, id=entry_id)
    
    if not entry.can_edit:
        return HttpResponseForbidden("You don't have permission to edit this entry")
    
    if request.method == 'POST':
        # Check if this is a summary generation request
        generate_summary = request.POST.get('generate_summary')
        if generate_summary:
            logger.info(f"Generating summary for {generate_summary}")
            if generate_summary == 'yesterday':
                summary = summarize_text(entry.yesterday)
                logger.info(f"Generated yesterday summary: {summary}")
                entry.yesterday_summary = summary
            elif generate_summary == 'today':
                summary = summarize_text(entry.today)
                logger.info(f"Generated today summary: {summary}")
                entry.today_summary = summary
            elif generate_summary == 'blockers' and entry.blockers:
                summary = summarize_text(entry.blockers)
                logger.info(f"Generated blockers summary: {summary}")
                entry.blockers_summary = summary
            entry.save()
            logger.info(f"Saved entry with summaries: yesterday={bool(entry.yesterday_summary)}, today={bool(entry.today_summary)}, blockers={bool(entry.blockers_summary)}")
            messages.success(request, 'Summary generated successfully!')
            return redirect('standup_list')
        
        # Regular edit request
        yesterday = request.POST.get('yesterday')
        today = request.POST.get('today')
        blockers = request.POST.get('blockers')
        status = request.POST.get('status')
        
        if not all([yesterday, today]):
            messages.error(request, 'Yesterday and Today fields are required')
            return render(request, 'core/standup_edit.html', {
                'entry': entry,
                'yesterday': yesterday,
                'today': today,
                'blockers': blockers,
                'status': status
            })
        
        # Generate summaries
        yesterday_summary = None
        today_summary = None
        blockers_summary = None
        
        entry.yesterday = yesterday
        entry.today = today
        entry.blockers = blockers
        entry.status = status
        entry.yesterday_summary = yesterday_summary
        entry.today_summary = today_summary
        entry.blockers_summary = blockers_summary
        entry.save()
        
        messages.success(request, 'Stand-up entry updated successfully!')
        return redirect('standup_list')
    
    return render(request, 'core/standup_edit.html', {'entry': entry})

@login_required
def standup_delete(request, entry_id):
    entry = get_object_or_404(StandUpEntry, id=entry_id)
    
    if not entry.can_delete:
        return HttpResponseForbidden("You don't have permission to delete this entry")
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Stand-up entry deleted successfully!')
        return redirect('standup_list')
    
    return render(request, 'core/standup_confirm_delete.html', {'entry': entry})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
    return render(request, 'core/logout_confirm.html')


