$("#delNotification").click(function (e) {
    e.preventDefault();
    $('#notificationDeleteModal').modal('show')

});

$("#addNotification").click(function (e) {
    e.preventDefault();
    CKEDITOR.replace('id_body_add');
    $('#addNewNotification').modal('show')
});