var tubes = [];
var markers = [];
var tubeDisplayed = false;

$(function () {
    var map;

    function initMap(location) {

	var mapCanvas = document.getElementById('map');
	var mapOptions = {
	    center: location,
	    zoom: 12,
	    panControl: false,
	    mapTypeId: google.maps.MapTypeId.ROADMAP
	}
	map = new google.maps.Map(mapCanvas, mapOptions);

	map.data.loadGeoJson('/static/zones.json');
	map.data.setStyle(function(feature) {
	  return /** @type {google.maps.Data.StyleOptions} */({
		cursor: 'auto',
		fillColor: feature.getProperty('fill'),
		strokeColor: feature.getProperty('stroke'),
		strokeWeight: feature.getProperty('stroke-width')
	  });
	});

	/*var markerImage = 'marker.png';

	  var marker = new google.maps.Marker({
position: location,
map: map//,
	//icon: markerImage
	});

	var contentString = '<div class="info-window">' +
	'<h3>Info Window Content</h3>' +
	'<div class="info-content">' +
	'<p>Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu libero sit amet quam egestas semper. Aenean ultricies mi vitae est. Mauris placerat eleifend leo.</p>' +
	'</div>' +
	'</div>';

	var infowindow = new google.maps.InfoWindow({
content: contentString,
maxWidth: 400
});

marker.addListener('click', function () {
infowindow.open(map, marker);
});*/

	var input = document.getElementById('pac-input');
	var searchBox = new google.maps.places.SearchBox(input);
    //map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);

	// Bias the SearchBox results towards current map's viewport.
	map.addListener('bounds_changed', function(event) {
	    searchBox.setBounds(map.getBounds());
	});

	// Listen for the event fired when the user selects a prediction and retrieve
	// more details for that place.
	searchBox.addListener('places_changed', function() {
	    var places = searchBox.getPlaces();

	    if (places.length == 0) {
			return;
	    }

	    // Clear out the old markers.
	    markers.forEach(function(marker) {
		marker.setMap(null);
	    });
	    markers = [];

	    // For each place, get the icon, name and location.
	    var bounds = new google.maps.LatLngBounds();
	    places.forEach(function(place) {
		if (!place.geometry) {
		    console.log("Returned place contains no geometry");
		    return;
		}
		//console.log(place.geometry.location.lat(), place.geometry.location.lng());
		/*var icon = {
url: place.icon,
size: new google.maps.Size(71, 71),
origin: new google.maps.Point(0, 0),
anchor: new google.maps.Point(17, 34),
scaledSize: new google.maps.Size(25, 25)
};

		// Create a marker for each place.
		markers.push(new google.maps.Marker({
map: map,
icon: icon,
title: place.name,
position: place.geometry.location
}));*/

		if (place.geometry.viewport) {
		    // Only geocodes have viewport.
		    bounds.union(place.geometry.viewport);
		} else {
		    bounds.extend(place.geometry.location);
		}

		var max_time = $('#max-time').val();

		var auto_load = $('#auto-load').is(':checked');
		$.get( "request", {
		    latitude: place.geometry.location.lat(), 
		    longitude: place.geometry.location.lng(), 
		    max_time: max_time * 60
		}, function(results) {
		    results.forEach(function(res){

			var location = new google.maps.LatLng(res.latitude, res.longitude);
			/*var marker = new google.maps.Marker({
position: location,
map: map
});

markers.push(marker);*/
			var circle = new google.maps.Circle({
			    strokeColor: '#FF0000',
			    strokeOpacity: 0.8,
			    strokeWeight: 2,
			    fillColor: '#FF0000',
			    fillOpacity: 0.05,
			    map: map,
			    center: {lat: res.latitude, lng: res.longitude},
			    radius: res.distance * 1000
			});
			markers.push(circle);

			if (auto_load) {
			    loadProperties({latitude: circle.getCenter().lat(), longitude: circle.getCenter().lng(), radius: circle.getRadius() / 1000}, map);
			} else {
				circle.addListener('click', function (event) {
					loadProperties({latitude: circle.getCenter().lat(), longitude: circle.getCenter().lng(), radius: circle.getRadius() / 1000}, map);
				});
			}
		    });

		}, "json");

		map.fitBounds(bounds);
		map.setZoom(12);
	    });
	});

    }

    $(document).ready(function(event) {
	//google.maps.event.addDomListener(window, 'domready', function(event){

	var location = new google.maps.LatLng(51.5098444,-0.143116);
	initMap(location);
	/*var geocoder = new google.maps.Geocoder();
	  geocoder.geocode({address: "London"}, function(results){
	  results.forEach(function(place) {

	  var location = new google.maps.LatLng(place.geometry.location.lat(), place.geometry.location.lng());

	  initMap(location);
	  });
	  });*/
    });

    $('form').on('submit', function(event){
		event.preventDefault();
		loc = $(this).find('[name=location]');

    });
	
	$('#toggle-tube').on('click', function(event){
	  if (tubes.length == 0) {
		loadTubes(map);
	  } else {
		if (tubeDisplayed) {
		  hideTubes();
		} else {
		  showTubes(map);
		}
	  }
	});
});

function loadTubes(map) {
    $.get( "tubes", {
    }, function(results) {
	  results.forEach(function(res){
		  var location = new google.maps.LatLng(res.latitude, res.longitude);
		  var marker = new google.maps.Marker({
			  position: location,
			  map: map
		  });
		  var icon = '/static/tube_small.png';

		  marker.setIcon({
			  url: icon,
			  scaledSize: new google.maps.Size(25, 20),
			  size: new google.maps.Size(100, 80),
			  anchor: new google.maps.Point(12, 10)
		  });

		  tubes.push(marker);
	  });
	  tubeDisplayed = true;
	}, "json");
}

function loadProperties(data, map) {

	var source = $('#source').val();

    var min_bed = $('#min-bed').val();
    var min_bath = $('#min-bath').val();
    var min_price = $('#min-price').val();
    var max_price = $('#max-price').val();

    $.get( "properties", {
		source: source,
		latitude: data.latitude,
		longitude: data.longitude,
		min_bed: min_bed,
		min_bath: min_bath,
		min_price: min_price,
		max_price: max_price,
		radius: data.radius
    }, function(results) {
	results.forEach(function(res){
	    var location = new google.maps.LatLng(res.latitude, res.longitude);
	    var marker = new google.maps.Marker({
			position: location,
			map: map
	    });

	    var price = Number(res.price).toLocaleString("en", {currency: "GBP", "style": "currency", "maximumFractionDigits": 0});

	    var floor_plans = '';
	    if (res.floor_plans != undefined) {
			res.floor_plans.forEach(function(floor_plan){
				floor_plans += '<a target="_blank" href="' + floor_plan + '">Plan</a><br/>';
			});
	    }
	    var contentString = 
		'<h3>' +
		'<a target="_blank" href="' + res.url + '">' + res.address + '</a>' +
		'</h3>' +
		'<div>' +
		'<img style="float: left; padding: 5px;" src="'+res.image+'" />' +
		'<b>' + price + '</b><br />' +
		floor_plans + " " +
		res.description +
		'</div>';

	    var infowindow = new google.maps.InfoWindow({
		content: contentString,
		maxWidth: 400
	    });

	    marker.addListener('click', function () {
		infowindow.open(map, marker);
	    });

	    markers.push(marker);
	});
    }, "json");
}

function hideTubes() {
  tubes.forEach(function(marker) {
	marker.setMap(null);
  });
  tubeDisplayed = false;
}

function showTubes(map) {
  tubes.forEach(function(marker) {
		marker.setMap(map);
  });
  tubeDisplayed = true;
}

