from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=200)
    matric_number = models.CharField(max_length=50)
    faculty = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    program = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class Level(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    level = models.IntegerField()
    gpa = models.FloatField(default=0)
    locked = models.BooleanField(default=False)


class Semester(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)  # First / Second
    gpa = models.FloatField(default=0)


class Course(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    unit = models.IntegerField()
    grade = models.CharField(max_length=2)