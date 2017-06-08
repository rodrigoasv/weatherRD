$(document).ready(function() {
	filterByMonth("");
});

function filterByCity(str) {
	var $rows = $('#table tbody tr');
	var val = str.replace(/ +/g, ' ').toLowerCase();
	$rows.show().filter(function() {
		var text = $(this).text().replace(/\s+/g, ' ').toLowerCase();
		return !~text.indexOf(val);
	}).hide();
	if (str == "")
		$('#dropdownCity').html("All " + '<span class="caret"></span>');
	else
		$('#dropdownCity').html(str + ' <span class="caret"></span>');
}

function filterByMonth(filter){
	$(".se-pre-con").show();
	$.ajax({
		url : "weather.py?" + filter,
		dataType: "text",
		success : function (data) {
			var obj = JSON.parse(data);
			$("#dropdownMonth").html(obj.text + ' <span class="caret"></span>');
			var filterItems = '';
			for (i = 0; i < obj.filter.length; i++) {
				filterItems += '<li><a href="javascript:void(0)" onclick="filterByMonth(\'' +
					obj.filter[i].param + '\')">' + obj.filter[i].label +'</a></li>';
			}
			$("#monthList").html(filterItems);
			
			// create title line
			var tableItems = '<thead id="header" bgcolor="#6B6C66"><tr>';
			for (i = 0; i < obj.table[0].length; i++) {
				tableItems += '<td align="center" style="padding:1px 4px"><b>' + obj.table[0][i] + '</b></td>';
			}
			tableItems += '</tr></thead><tbody id="t-data">';
			
			// create data lines
			for (i = 1; i < obj.table.length; i++) {
				tableItems += '<tr>';
				for (j = 0; j < obj.table[i].length; j++) {
					tableItems += '<td align="center" style="padding:1px 4px">' + obj.table[i][j] + '</td>';
				}
				tableItems += '</tr>';
			}
			tableItems += '</tbody>';
			$("#table").html(tableItems);

			// Remakes the list of cities available for filtering
			$("#cityList").empty();
			addCity('""', "All");
			var listCity = $('#table tbody tr td:nth-child(2)');
			var cities = [];
			for (i = 0; i < listCity.length; i++) {
				if (cities.indexOf(listCity[i].innerText) == -1) {
					cities.push(listCity[i].innerText);
					addCity("this.innerHTML", listCity[i].innerText);
				}
			}
			$(".se-pre-con").fadeOut("slow");
		},
	});
	$('#dropdownCity').html("Filter by City " + '<span class="caret"></span>');
}

function addCity(filter, nameText){
	var ulcity = document.getElementById("cityList");
	var li = document.createElement("li");
	var a = document.createElement("a");
	a.setAttribute("href", "javascript:void(0)");
	a.setAttribute("onclick", "filterByCity(" + filter + ")");
	a.appendChild(document.createTextNode(nameText));
	li.appendChild(a);
	ulcity.appendChild(li);
}
