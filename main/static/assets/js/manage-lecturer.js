$("#addLecturer").click(function (e) {
    e.preventDefault();
    $('#addNewLecturerModal').modal('show')
});

$("#deleteLecturer").click(function (e) {
    e.preventDefault();
    $('#confirmDeleteModal').modal('show')
});