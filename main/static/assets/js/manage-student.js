$("#deleteStudent").click(function (e) {
    e.preventDefault();
});

function confirmDelete(studentId) {
    var deleteUrl = "{% url 'admin_student_delete' '1' %}".replace('1', studentId);
    $('#confirmDeleteButton').attr('href', deleteUrl);
    $('#confirmDeleteModal').modal('show');
    $('#studentIdToDelete').text(studentId);
}

$("#addStudent").click(function (e) {
    e.preventDefault();
    $('#addNewStudentModal').modal('show')
});

$("#editStudent").click(function (e) {
    e.preventDefault();
});

function editStudent(studentId) {
    var editUrl = "admin/student-management/edit/1".replace('1', studentId);
    $('#editStudentModal').modal('show');
}