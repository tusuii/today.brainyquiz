from flask import Blueprint, jsonify
from flask_login import login_required
from app.routes.admin import admin_required
from app.models import Quiz, Question, UserQuiz, UserAnswer, User
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

api = Blueprint('api', __name__)

@api.route('/quiz-completion-rate')
@login_required
@admin_required
def quiz_completion_rate():
    """API endpoint to get quiz completion rates for chart"""
    # Get all quizzes
    quizzes = Quiz.query.all()
    
    data = []
    for quiz in quizzes:
        # Count total attempts
        total_attempts = UserQuiz.query.filter_by(quiz_id=quiz.id).count()
        
        # Count completed attempts
        completed_attempts = UserQuiz.query.filter_by(quiz_id=quiz.id).filter(UserQuiz.completed_at.isnot(None)).count()
        
        # Calculate completion rate
        completion_rate = 0
        if total_attempts > 0:
            completion_rate = (completed_attempts / total_attempts) * 100
            
        data.append({
            'quiz_title': quiz.title,
            'completion_rate': round(completion_rate, 1)
        })
    
    return jsonify(data)

@api.route('/average-scores')
@login_required
@admin_required
def average_scores():
    """API endpoint to get average scores per quiz"""
    quizzes = Quiz.query.all()
    
    data = []
    for quiz in quizzes:
        # Get all completed attempts for this quiz
        attempts = UserQuiz.query.filter_by(quiz_id=quiz.id).filter(UserQuiz.completed_at.isnot(None)).all()
        
        # Calculate average score
        if attempts:
            total_score = sum(attempt.score for attempt in attempts)
            avg_score = total_score / len(attempts)
            
            # Get total possible score (number of questions)
            question_count = Question.query.filter_by(quiz_id=quiz.id).count()
            
            # Calculate percentage
            percentage = 0
            if question_count > 0:
                percentage = (avg_score / question_count) * 100
                
            data.append({
                'quiz_title': quiz.title,
                'avg_score_percentage': round(percentage, 1)
            })
    
    return jsonify(data)

@api.route('/time-distribution')
@login_required
@admin_required
def time_distribution():
    """API endpoint to get time distribution for quiz completion"""
    # Get all completed quizzes
    completed_quizzes = UserQuiz.query.filter(UserQuiz.completed_at.isnot(None)).all()
    
    # Time ranges in minutes
    time_ranges = {
        'Under 5 min': 0,
        '5-10 min': 0,
        '10-15 min': 0,
        '15-30 min': 0,
        'Over 30 min': 0
    }
    
    for quiz in completed_quizzes:
        # Calculate duration in minutes
        duration = (quiz.completed_at - quiz.created_at).total_seconds() / 60
        
        if duration < 5:
            time_ranges['Under 5 min'] += 1
        elif duration < 10:
            time_ranges['5-10 min'] += 1
        elif duration < 15:
            time_ranges['10-15 min'] += 1
        elif duration < 30:
            time_ranges['15-30 min'] += 1
        else:
            time_ranges['Over 30 min'] += 1
    
    # Format data for chart
    data = [
        {'range': key, 'count': value}
        for key, value in time_ranges.items()
    ]
    
    return jsonify(data)

@api.route('/user-performance')
@login_required
@admin_required
def user_performance():
    """API endpoint to get top 10 users by average score"""
    # Get users with completed quizzes
    users = User.query.join(UserQuiz).filter(UserQuiz.completed_at.isnot(None)).distinct().all()
    
    user_data = []
    for user in users:
        # Get all completed quizzes for this user
        completed_quizzes = UserQuiz.query.filter_by(user_id=user.id).filter(UserQuiz.completed_at.isnot(None)).all()
        
        if completed_quizzes:
            # Calculate average score percentage
            total_percentage = 0
            for quiz in completed_quizzes:
                question_count = Question.query.filter_by(quiz_id=quiz.quiz_id).count()
                if question_count > 0:
                    percentage = (quiz.score / question_count) * 100
                    total_percentage += percentage
            
            avg_percentage = total_percentage / len(completed_quizzes)
            
            user_data.append({
                'username': user.username,
                'avg_score': round(avg_percentage, 1),
                'quizzes_taken': len(completed_quizzes)
            })
    
    # Sort by average score and get top 10
    user_data.sort(key=lambda x: x['avg_score'], reverse=True)
    top_users = user_data[:10]
    
    return jsonify(top_users)

@api.route('/activity-over-time')
@login_required
@admin_required
def activity_over_time():
    """API endpoint to get quiz activity over time (last 30 days)"""
    # Get date 30 days ago
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Get all quiz attempts in the last 30 days
    recent_attempts = UserQuiz.query.filter(UserQuiz.created_at >= thirty_days_ago).all()
    
    # Group by day
    daily_counts = {}
    for attempt in recent_attempts:
        day = attempt.created_at.strftime('%Y-%m-%d')
        if day not in daily_counts:
            daily_counts[day] = 0
        daily_counts[day] += 1
    
    # Fill in missing days
    current_date = thirty_days_ago
    end_date = datetime.now()
    all_days = {}
    
    while current_date <= end_date:
        day_str = current_date.strftime('%Y-%m-%d')
        all_days[day_str] = daily_counts.get(day_str, 0)
        current_date += timedelta(days=1)
    
    # Format for chart
    data = [
        {'date': key, 'attempts': value}
        for key, value in all_days.items()
    ]
    
    return jsonify(data)
