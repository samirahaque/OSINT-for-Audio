function sortTable(columnIndex) {
    var table = document.getElementById("myTable");
    var rowsArray = Array.from(table.rows).slice(1); // Convert rows to array, excluding the header
    var dir = table.getAttribute("data-sort-dir") === "asc" ? "desc" : "asc";
    // Sort rows array
    rowsArray.sort(function(a, b) {
        var x = a.getElementsByTagName("TD")[columnIndex].textContent.toLowerCase();
        var y = b.getElementsByTagName("TD")[columnIndex].textContent.toLowerCase();
        return dir === "asc" ? (x > y ? 1 : -1) : (x < y ? 1 : -1);
    });
    // Reattach rows in sorted order
    rowsArray.forEach(row => table.appendChild(row));
    // Update table sort direction
    table.setAttribute("data-sort-dir", dir);
    // Update visual indicators
    updateSortArrow(columnIndex, dir);
}

function updateSortArrow(columnIndex, dir) {
    var ths = document.querySelectorAll(".agents-table thead th");
    ths.forEach((th, index) => {
        th.classList.remove("sort-asc", "sort-desc");
        if (index === columnIndex) {
            th.classList.add(dir === "asc" ? "sort-asc" : "sort-desc");
        }
    });
}
