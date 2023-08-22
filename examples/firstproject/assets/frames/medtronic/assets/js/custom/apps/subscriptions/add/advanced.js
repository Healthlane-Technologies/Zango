"use strict";

var KTSubscriptionsAdvanced = function () {
    // Shared variables
    var table;
    var datatable;

    var initCustomFieldsDatatable = function () {
        // Define variables
        const addButton = document.getElementById('kt_create_new_custom_fields_add');

        // Duplicate input fields
        const fieldName = table.querySelector('tbody tr td:first-child').innerHTML;
        const fieldValue = table.querySelector('tbody tr td:nth-child(2)').innerHTML;
        const deleteButton = table.querySelector('tbody tr td:last-child').innerHTML;

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        datatable = $(table).DataTable({
            "info": false,
            'order': [],
            'ordering': false,
            'paging': false,
            "lengthChange": false
        });

        // Define datatable row node
        var rowNode;

        // Handle add button
        addButton.addEventListener('click', function (e) {
            e.preventDefault();

            rowNode = datatable.row.add([
                fieldName,
                fieldValue,
                deleteButton
            ]).draw().node();

            // Add custom class to last column -- more info: https://datatables.net/forums/discussion/22341/row-add-cell-class
            $(rowNode).find('td').eq(2).addClass('text-end');

            // Re-calculate index
            initCustomFieldRowIndex();
        });
    }

    // Handle row index count
    var initCustomFieldRowIndex = function() {
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach((tr, index) => {
            // add index number to input names & id
            const fieldNameInput = tr.querySelector('td:first-child input');
            const fieldValueInput = tr.querySelector('td:nth-child(2) input');
            const fieldNameLabel = fieldNameInput.getAttribute('id');
            const fieldValueLabel = fieldValueInput.getAttribute('id');

            fieldNameInput.setAttribute('name', fieldNameLabel + '-' + index);
            fieldValueInput.setAttribute('name', fieldValueLabel + '-' + index);
        });
    }

    // Delete product
    var deleteCustomField = function() {
        KTUtil.on(table, '[data-kt-action="field_remove"]', 'click', function(e) {
            e.preventDefault();

            // Select parent row
            const parent = e.target.closest('tr');

            // SweetAlert2 pop up --- official docs reference: https://sweetalert2.github.io/
            Swal.fire({
                text: "Are you sure you want to delete this field ?",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "Yes, delete!",
                cancelButtonText: "No, cancel",
                customClass: {
                    confirmButton: "btn fw-bold btn-danger",
                    cancelButton: "btn fw-bold btn-active-light-primary"
                }
            }).then(function (result) {
                if (result.value) {
                    Swal.fire({
                        text: "You have deleted it!.",
                        icon: "success",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn fw-bold btn-primary",
                        }
                    }).then(function () {
                        // Remove current row
                        datatable.row($(parent)).remove().draw();
                    });
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "It was not deleted.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn fw-bold btn-primary",
                        }
                    })
                }
            });
        });
    }

    return {
        init: function () {
            table = document.getElementById('kt_create_new_custom_fields');

            initCustomFieldsDatatable();
            initCustomFieldRowIndex();            
            deleteCustomField();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTSubscriptionsAdvanced.init();
});