"use strict";

// Class definition
var KTCustomerViewInvoices = function () {

    // Private functions
    // Init current year datatable
    var initInvoiceYearCurrent = function () {
        // Define table element
        const id = '#kt_customer_details_invoices_table_1';
        var table = document.querySelector(id);

        // Set date data order
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[0].innerHTML, "DD MMM YYYY, LT").format(); // select date from 1st column in table
            dateRow[0].setAttribute('data-order', realDate);
        });

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        var datatable = $(id).DataTable({
            "info": false,
            'order': [],
            "pageLength": 5,
            "lengthChange": false,
            'columnDefs': [
                { orderable: false, targets: 4 }, // Disable ordering on column 0 (download)
            ]
        });
    }

    // Init year 2020 datatable
    var initInvoiceYear2020 = function () {
        // Define table element
        const id = '#kt_customer_details_invoices_table_2';
        var table = document.querySelector(id);

        // Set date data order
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[0].innerHTML, "DD MMM YYYY, LT").format(); // select date from 1st column in table
            dateRow[0].setAttribute('data-order', realDate);
        });

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        var datatable = $(id).DataTable({
            "info": false,
            'order': [],
            "pageLength": 5,
            "lengthChange": false,
            'columnDefs': [
                { orderable: false, targets: 4 }, // Disable ordering on column 0 (download)
            ]
        });
    }

    // Init year 2019 datatable
    var initInvoiceYear2019 = function () {
        // Define table element
        const id = '#kt_customer_details_invoices_table_3';
        var table = document.querySelector(id);

        // Set date data order
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[0].innerHTML, "DD MMM YYYY, LT").format(); // select date from 1st column in table
            dateRow[0].setAttribute('data-order', realDate);
        });

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        var datatable = $(id).DataTable({
            "info": false,
            'order': [],
            "pageLength": 5,
            "lengthChange": false,
            'columnDefs': [
                { orderable: false, targets: 4 }, // Disable ordering on column 0 (download)
            ]
        });
    }

    // Init year 2018 datatable
    var initInvoiceYear2018 = function () {
        // Define table element
        const id = '#kt_customer_details_invoices_table_4';
        var table = document.querySelector(id);

        // Set date data order
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[0].innerHTML, "DD MMM YYYY, LT").format(); // select date from 1st column in table
            dateRow[0].setAttribute('data-order', realDate);
        });

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        var datatable = $(id).DataTable({
            "info": false,
            'order': [],
            "pageLength": 5,
            "lengthChange": false,
            'columnDefs': [
                { orderable: false, targets: 4 }, // Disable ordering on column 0 (download)
            ]
        });
    }

    // Public methods
    return {
        init: function () {
            initInvoiceYearCurrent();
            initInvoiceYear2020();
            initInvoiceYear2019();
            initInvoiceYear2018();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTCustomerViewInvoices.init();
});