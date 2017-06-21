addCities("");

function addCities(filter){
	$.ajax({
		url : "raindays.py?" + filter,
		dataType: "text",
		success : function (data) {
			var obj = JSON.parse(data);
			$("#dropdownCity").html(obj.text + ' <span class="caret"></span>');
			
			var filterItems = '';
			for (i = 0; i < obj.cities.length; i++) {
				filterItems += '<li><a href="javascript:void(0)" onclick="addCities(\'' +
					obj.cities[i].id + '\')">' + obj.cities[i].name +'</a></li>';
			}
			$("#cityList").html(filterItems);
			var obj = JSON.parse(data);
			var dict = {};
			for (i = 0; i < obj.days.length; i++) {
				dict[new Date(obj.days[i].year, obj.days[i].month, obj.days[i].day).getTime()] = true;
			}
			$('#calendar').calendar({ 
				customDayRenderer: function(element, date) {
					if (date.getTime() in dict) {
						$(element).css('background-color', 'blue');
						$(element).css('color', 'white');
						$(element).css('border-radius', '15px');
					}
				}
			});
			$('#calendar').data('calendar').setMinDate(new Date(2017, 2, 1));
			$('#calendar').data('calendar').setMaxDate(new Date());
		}
	});
}