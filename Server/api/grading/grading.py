class AutoGradePro:
    def __init__(self, stu_file_name, tea_file_name):
        """
        Initializes AutoGradePro with file names for student and teacher answer files.
        """
        self.stu_file_name = stu_file_name
        self.tea_file_name = tea_file_name

    def content(self):
        """
        Reads and returns the content of the student answer file as a list.
        Each line is stripped of newline characters.
        """
        content = []
        with open(self.stu_file_name) as file:
            for line in file:
                content.append(line.strip())
        return content

    def answerScheme(self):
        """
        Reads and returns the teacher's marking scheme from the answer file.
        The first line is treated as the teacher's ID, and the following lines contain
        question numbers, correct answers, and allocated marks.
        """
        inside_doc = []
        with open(self.tea_file_name) as file:
            for line in file:
                inside_doc.append(line.strip())
        teach_id = inside_doc[0]

        # Parse each line after the teacher ID to get question number, answer, and marks
        teacher_answers = [(int(item.split()[0]), item.split()[1], int(item.split()[2]))
                           for item in inside_doc[1:]]

        return Scheme(teach_id, teacher_answers)

    def virtAnswSheet(self):
        """
        Creates and returns a virtual answer sheet for the student.
        The first line in the student file is the index number, and the rest are answers.
        """
        # Extract index number from the first line of the file content
        index_no = self.content()[0]

        # Extract answers from the remaining lines
        answers = [(int(item.split()[0]), item.split()[1]) for item in self.content()[1:]]

        # Return an AnswerSheet instance with index number and answers list
        return AnswerSheet(index_no, answers)

    def printvirtAnswSheet(self):
        """
        Prints the student's virtual answer sheet in a formatted way.
        Displays the index number and each question with its corresponding answer.
        """
        answer_sheet = self.virtAnswSheet()
        print("Index No:", answer_sheet.index_no)
        for question_no, answer in answer_sheet.complete_answers:
            print(f"Q{question_no} => {answer}")

    def printScheme(self):
        """
        Prints the teacher's marking scheme.
        Shows the teacher ID, question numbers, correct answers, and allocated marks.
        """
        marking_scheme = self.answerScheme()
        print("Teacher ID:", marking_scheme.tea_id)
        for question_no, answer, allocated_marks in marking_scheme.teacher_answer:
            print(f"Q{question_no} => {answer} => {allocated_marks}")

    def generateReport(self):
        """
        Compares the student's answers with the teacher's marking scheme to generate a report.
        Returns a ReportSheet instance containing the student's index number, answer status, and total marks.
        """
        # Get the student's answer sheet and teacher's marking scheme
        stu_answer_sheet = self.virtAnswSheet()
        correct_answer = self.answerScheme()
        total_marks = 0
        answer_status = []

        # Compare each student answer to the corresponding teacher answer
        for stu_answer in stu_answer_sheet.complete_answers:
            question_no, stu_ans = stu_answer
            teacher_answer = next((ans for q_no, ans, marks in correct_answer.teacher_answer if q_no == question_no),
                                  None)
            allocated_marks = next((marks for q_no, ans, marks in correct_answer.teacher_answer if q_no == question_no),
                                   0)

            # Check if the answer is correct and accumulate marks
            if stu_ans == teacher_answer:
                answer_status.append((question_no, stu_ans, teacher_answer, 'Correct', allocated_marks))
                total_marks += allocated_marks
            else:
                answer_status.append((question_no, stu_ans, teacher_answer, 'Incorrect', 0))

        # Create the final report as a ReportSheet instance
        final_report = ReportSheet(stu_answer_sheet.index_no, answer_status, total_marks)
        return final_report  # Return the report for further use


class AnswerSheet:
    def __init__(self, index_no, complete_answers):
        """
        Represents a student's answer sheet.

        Parameters:
        - index_no: Student's unique identification number.
        - complete_answers: List of tuples containing question number and the student's answer.
        """
        self.index_no = index_no
        self.complete_answers = complete_answers


class ReportSheet:
    def __init__(self, index_no, answer_status, total_marks):
        """
        Represents a report for a student's answer sheet evaluation.

        Parameters:
        - index_no: Student's unique identification number.
        - answer_status: List of tuples for each question (question number, student answer, correct answer, status, marks).
        - total_marks: Total marks obtained by the student.
        """
        self.index_no = index_no
        self.answer_status = answer_status
        self.total_marks = total_marks

    def print_report(self):
        """
        Prints the report in a structured format, showing each question's details and the total marks.
        """
        print("Report for Student Index No:", self.index_no)
        print("Question | Student Answer | Correct Answer | Status   | Marks")
        print("-" * 60)
        for question_no, stu_answer, correct_answer, status, marks in self.answer_status:
            print(f"Q{question_no}      | {stu_answer}            | {correct_answer}           | {status}    | {marks}")
        print(f"Total Marks: {self.total_marks}")


class Scheme:
    def __init__(self, tea_id, teacher_answer):
        """
        Represents the teacher's answer scheme.

        Parameters:
        - tea_id: Unique identification for the teacher.
        - teacher_answer: List of tuples containing question number, correct answer, and allocated marks.
        """
        self.tea_id = tea_id
        self.teacher_answer = teacher_answer


tes = AutoGradePro("../migrations/student_answer.txt", "teacher_ answer.txt")
tes.printvirtAnswSheet()
print("===========================")
tes.printScheme()
print("===========================")
report = tes.generateReport()  # Generates and returns the report
report.print_report()
