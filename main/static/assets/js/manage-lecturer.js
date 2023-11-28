$("#addSchedule").click(function (e) {
    e.preventDefault();
    $('#addNewScheduleModal').modal('show')
});

$("#editSchedule").click(function (e) {
    e.preventDefault();
    $('#editScheduleModal').modal('show')
});

$("#deleteLecturer").click(function (e) {
    e.preventDefault();
    $('#confirmDeleteModal').modal('show')
});