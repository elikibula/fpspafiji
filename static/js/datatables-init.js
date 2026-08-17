document.addEventListener("DOMContentLoaded", () => {
    if (typeof DataTable === "undefined") {
        return;
    }

    document.querySelectorAll("table").forEach((table) => {
        if (table.dataset.datatable === "false" || table.classList.contains("dataTable")) {
            return;
        }

        const columnCount = table.tHead?.rows[0]?.cells.length ?? 0;
        if (!columnCount) {
            return;
        }

        // Replace Django's colspan-based empty-state rows with DataTables' empty state.
        // DataTables requires each tbody row to have the same number of cells as the header.
        Array.from(table.tBodies).forEach((body) => {
            Array.from(body.rows).forEach((row) => {
                const isTabularRow = row.cells.length === columnCount &&
                    Array.from(row.cells).every((cell) => cell.colSpan === 1);
                if (!isTabularRow) {
                    row.remove();
                }
            });
        });

        const actionColumns = Array.from(table.tHead.rows[0].cells)
            .map((cell, index) => ({ index, label: cell.textContent.trim().toLowerCase() }))
            .filter(({ label }) => label === "action" || label === "actions")
            .map(({ index }) => index);

        Array.from(table.tHead.rows[0].cells).forEach((cell, index) => {
            if (!actionColumns.includes(index)) {
                cell.title = `Sort by ${cell.textContent.trim()}`;
            }
        });

        new DataTable(table, {
            // Full interactive DataTables behavior: sortable fields and client-side pages.
            paging: true,
            pageLength: 10,
            lengthMenu: [10, 25, 50, 100],
            searching: true,
            ordering: true,
            autoWidth: false,
            order: [],
            columnDefs: actionColumns.length
                ? [{ targets: actionColumns, orderable: false, searchable: false }]
                : [],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                emptyTable: "No records available",
                zeroRecords: "No matching records found"
            }
        });
    });
});
