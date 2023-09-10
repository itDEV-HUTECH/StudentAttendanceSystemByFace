from django.db import models


# Create your models here.
class TrainingDepartmentInfo(models.Model):
    id_staff = models.CharField(max_length=10, primary_key=True)
    staff_name = models.TextField()
    email = models.TextField()
    phone = models.TextField()
    address = models.TextField()
    birthday = models.TextField()
    password = models.CharField(max_length=16)


class LecturerInfo(models.Model):
    id_lecturer = models.CharField(max_length=10, primary_key=True)
    lecturer_name = models.TextField()
    email = models.TextField()
    phone = models.TextField()
    address = models.TextField()
    birthday = models.TextField()
    password = models.CharField(max_length=16)


class StudentInfo(models.Model):
    id_student = models.CharField(max_length=10, primary_key=True)
    student_name = models.TextField()
    email = models.TextField()
    phone = models.TextField()
    address = models.TextField()
    birthday = models.TextField()
    PathImageFolder = models.TextField()
    password = models.CharField(max_length=16)


class Classroom(models.Model):
    id_classroom = models.BigAutoField(primary_key=True)
    name = models.TextField()
    begin_date = models.DateField()
    end_date = models.DateField()
    begin_time = models.TimeField()
    end_time = models.TimeField()
    id_lecturer = models.ForeignKey(
        LecturerInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    students = models.ManyToManyField(StudentInfo, through='StudentClassDetails')


class StudentClassDetails(models.Model):
    id_classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    id_student = models.ForeignKey(StudentInfo, on_delete=models.CASCADE)


class Attendance(models.Model):
    id_attendance = models.BigAutoField(primary_key=True)
    check_in_time = models.DateTimeField()
    attendance_status_bit = models.BooleanField()
    id_classroom = models.ForeignKey('Classroom', on_delete=models.SET_NULL, null=True)
    id_student = models.ForeignKey('StudentInfo', on_delete=models.CASCADE)
