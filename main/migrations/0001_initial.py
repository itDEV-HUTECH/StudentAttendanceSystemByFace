# Generated by Django 5.0a1 on 2023-10-31 16:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='StaffInfo',
            fields=[
                ('id_staff', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('staff_name', models.TextField()),
                ('email', models.TextField()),
                ('phone', models.TextField()),
                ('address', models.TextField()),
                ('birthday', models.DateField()),
                ('password', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='StudentInfo',
            fields=[
                ('id_student', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('student_name', models.TextField()),
                ('email', models.TextField()),
                ('phone', models.TextField()),
                ('address', models.TextField()),
                ('birthday', models.DateField()),
                ('PathImageFolder', models.TextField()),
                ('password', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id_classroom', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('begin_date', models.DateField()),
                ('end_date', models.DateField()),
                ('day_of_week_begin', models.IntegerField()),
                ('begin_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('id_lecturer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.staffinfo')),
            ],
        ),
        migrations.CreateModel(
            name='StaffRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.role')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.staffinfo')),
            ],
        ),
        migrations.AddField(
            model_name='staffinfo',
            name='roles',
            field=models.ManyToManyField(related_name='staff_role', through='main.StaffRole', to='main.role'),
        ),
        migrations.CreateModel(
            name='StudentClassDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.classroom')),
                ('id_student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.studentinfo')),
            ],
        ),
        migrations.AddField(
            model_name='classroom',
            name='students',
            field=models.ManyToManyField(through='main.StudentClassDetails', to='main.studentinfo'),
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id_attendance', models.BigAutoField(primary_key=True, serialize=False)),
                ('check_in_time', models.DateTimeField()),
                ('attendance_status', models.IntegerField()),
                ('id_classroom', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.classroom')),
                ('id_student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.studentinfo')),
            ],
        ),

    ]
