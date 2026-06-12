import re
from dataclasses import dataclass
from typing import List, Optional

# --- 1. ĐỊNH NGHĨA CẤU TRÚC DỮ LIỆU ---
@dataclass
class Subject:
    stt: int
    course_code: str
    course_name: str
    score: Optional[float]  # Thang 10
    letter_grade: str
    credits: int
    note: str
    score_4: Optional[float] = None # Thang 4

@dataclass
class Semester:
    name: str
    subjects: List[Subject]
    
    def calculate_semester_gpa(self):
        # Hệ số điểm chữ sang hệ 4.0 của Bách Khoa
        grade_scale = {
            'A+': 4.0, 'A': 4.0, 
            'B+': 3.5, 'B': 3.0, 
            'C+': 2.5, 'C': 2.0, 
            'D+': 1.5, 'D': 1.0, 
            'F': 0.0, 'KD': 0.0
        }
        
        total_points = 0
        total_credits = 0
        
        for sub in self.subjects:
            # Bỏ qua môn 0 tín chỉ hoặc các môn rút/miễn/đạt (RT, MT, DT...)
            if sub.credits == 0 or sub.letter_grade not in grade_scale:
                continue
                
            point = grade_scale[sub.letter_grade]
            total_points += point * sub.credits
            total_credits += sub.credits
            
        return round(total_points / total_credits, 2) if total_credits > 0 else 0.0

@dataclass
class Transcript:
    student_name: str
    student_id: str
    semesters: List[Semester]

# --- 2. HÀM PARSER ---
def parse_mybk_transcript_text(text: str) -> Transcript:
    lines = text.splitlines()
    student_name = ""
    student_id = ""
    semesters = []
    current_semester = None
    
    # Regex xử lý linh hoạt khoảng trắng (Space) hoặc Tab (\t) giữa các cột
    # Nhóm 1: STT | Nhóm 2: Mã môn | Nhóm 3: Tên môn | Nhóm 4: Điểm | Nhóm 5: Điểm chữ | Nhóm 6: TC | Nhóm 7: Note
    subject_pattern = re.compile(r'^(\d+)\s+([A-Z0-9]+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+([A-Z][+-]?|RT|DT|MT|CH|KD|VT|CT|VP|HT)\s+(\d)(.*)$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Trích xuất thông tin cá nhân
        if "Họ và tên:" in line:
            student_name = line.split("Họ và tên:")[1].strip().split('\t')[0]
        elif "Mã sinh viên:" in line:
            student_id = line.split("Mã sinh viên:")[1].strip().split('\t')[0]
        elif line.startswith("User Image") and not student_name:
            # Fallback cho trường hợp copy thô từ web
            student_name = line.replace("User Image", "").strip()
            
        # Trích xuất Header của học kỳ
        elif line.startswith("Năm học") and "Học kỳ" in line:
            sem_name = line.split('\t')[0].strip()
            current_semester = Semester(name=sem_name, subjects=[])
            semesters.append(current_semester)
            
        # Xử lý khối môn học chuyển/miễn điểm ở cuối bảng
        elif line.startswith("Môn học chuyển điểm/miễn điểm"):
            current_semester = Semester(name="Môn học chuyển điểm/miễn điểm", subjects=[])
            semesters.append(current_semester)
            
        # Trích xuất chi tiết từng môn học 
        else:
            match = subject_pattern.match(line)
            if match and current_semester is not None:
                stt = int(match.group(1))
                course_code = match.group(2)
                course_name = match.group(3).strip()
                
                score_str = match.group(4)
                score = float(score_str) if score_str else None
                
                letter_grade = match.group(5)
                credits = int(match.group(6))
                
                # Dọn dẹp khoảng trắng và tab ở phần ghi chú
                note = match.group(7).replace('\t', ' ').strip()
                
                subject = Subject(stt, course_code, course_name, score, letter_grade, credits, note)
                current_semester.subjects.append(subject)

    return Transcript(student_name, student_id, semesters)

def parse_mybk_transcript_file(file_path: str) -> Transcript:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return parse_mybk_transcript_text(content)
    except FileNotFoundError:
        return None
