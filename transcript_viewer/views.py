from django.shortcuts import render, redirect
import os
from parser import parse_mybk_transcript_text, Subject

def get_grade_info(score_10=None, score_4=None, letter=None):
    grade_map = [
        {'letter': 'A+', 's4': 4.0, 's10_min': 9.0},
        {'letter': 'A',  's4': 4.0, 's10_min': 8.5},
        {'letter': 'B+', 's4': 3.5, 's10_min': 8.0},
        {'letter': 'B',  's4': 3.0, 's10_min': 7.0},
        {'letter': 'C+', 's4': 2.5, 's10_min': 6.5},
        {'letter': 'C',  's4': 2.0, 's10_min': 5.5},
        {'letter': 'D+', 's4': 1.5, 's10_min': 5.0},
        {'letter': 'D',  's4': 1.0, 's10_min': 4.0},
        {'letter': 'F',  's4': 0.0, 's10_min': 0.0},
    ]
    
    if score_10 is not None:
        for g in grade_map:
            if score_10 >= g['s10_min']:
                return g['letter'], g['s4'], score_10
    elif score_4 is not None:
        for g in grade_map:
            if score_4 == g['s4']:
                return g['letter'], score_4, g['s10_min']
    elif letter is not None:
        for g in grade_map:
            if letter == g['letter']:
                return letter, g['s4'], g['s10_min']
    
    return 'F', 0.0, 0.0

def transcript_view(request):
    if 'manual_subjects' not in request.session or not isinstance(request.session['manual_subjects'], dict):
        request.session['manual_subjects'] = {}
    
    # Không còn fallback lấy từ file bang_diem.txt nữa
    if 'pasted_transcript' not in request.session:
        request.session['pasted_transcript'] = None

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'clear':
            request.session['manual_subjects'] = {}
            request.session['pasted_transcript'] = None
            request.session.modified = True
            return redirect('transcript_view')
            
        elif action == 'paste':
            raw_text = request.POST.get('raw_text', '')
            transcript_obj = parse_mybk_transcript_text(raw_text)
            if transcript_obj:
                sem_list = []
                for sem in transcript_obj.semesters:
                    sub_list = []
                    for s in sem.subjects:
                        sub_list.append({
                            'stt': s.stt, 'course_code': s.course_code, 'course_name': s.course_name,
                            'score': s.score, 'letter_grade': s.letter_grade, 'credits': s.credits, 'note': s.note
                        })
                    sem_list.append({'name': sem.name, 'subjects': sub_list})
                
                request.session['pasted_transcript'] = {
                    'student_name': transcript_obj.student_name,
                    'student_id': transcript_obj.student_id,
                    'semesters': sem_list
                }
                request.session.modified = True
            return redirect('transcript_view')

        # Xử lý thêm/sửa môn
        c_code = request.POST.get('code')
        c_name = request.POST.get('name')
        c_credits = int(request.POST.get('credits', 0))
        s10 = request.POST.get('score10')
        s4 = request.POST.get('score4')
        
        if s10:
            letter, score4, score10 = get_grade_info(score_10=float(s10))
        elif s4:
            letter, score4, score10 = get_grade_info(score_4=float(s4))
        else:
            letter, score4, score10 = 'F', 0.0, 0.0

        request.session['manual_subjects'][c_code] = {
            'course_code': c_code, 'course_name': c_name, 'score': score10,
            'score_4': score4, 'letter_grade': letter, 'credits': c_credits, 'note': 'Thủ công'
        }
        request.session.modified = True
        return redirect('transcript_view')

    # Xây dựng danh sách hiển thị
    pasted = request.session.get('pasted_transcript')
    grade_scale = {'A+': 4.0, 'A': 4.0, 'B+': 3.5, 'B': 3.0, 'C+': 2.5, 'C': 2.0, 'D+': 1.5, 'D': 1.0, 'F': 0.0}
    best_subjects = {}

    if pasted:
        for sem in pasted['semesters']:
            if sem['name'] == "Môn học chuyển điểm/miễn điểm": continue
            for sub in sem['subjects']:
                if sub['letter_grade'] in ['RT', 'DT']: continue
                
                s4 = grade_scale.get(sub['letter_grade'], 0.0)
                code = sub['course_code']
                
                # Giả lập Object để dùng logic cũ
                sub_obj = Subject(sub['stt'], code, sub['course_name'], sub['score'], sub['letter_grade'], sub['credits'], sub['note'], s4)
                
                if code not in best_subjects or s4 > grade_scale.get(best_subjects[code].letter_grade, -1.0):
                    best_subjects[code] = sub_obj

    # Ghi đè thủ công
    for code, sub_dict in request.session['manual_subjects'].items():
        best_subjects[code] = Subject(999, code, sub_dict['course_name'], sub_dict['score'], sub_dict['letter_grade'], sub_dict['credits'], sub_dict['note'], sub_dict['score_4'])

    all_subjects = list(best_subjects.values())
    all_subjects.sort(key=lambda x: x.course_name.lower())
    
    total_points = sum(s.score_4 * s.credits for s in all_subjects if s.letter_grade in grade_scale)
    total_credits = sum(s.credits for s in all_subjects if s.letter_grade in grade_scale)
    overall_gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        
    context = {
        'student_name': pasted['student_name'] if pasted else None,
        'student_id': pasted['student_id'] if pasted else None,
        'subjects': all_subjects,
        'overall_gpa': overall_gpa,
        'total_credits': total_credits
    }
    return render(request, 'transcript_viewer/transcript.html', context)
