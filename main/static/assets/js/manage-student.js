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