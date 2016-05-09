var getRandomColor = function(){
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;	
};

var getRandomColorAsList = function(){
    var color = [];
    return [
		Math.floor(Math.random() * 256),
		Math.floor(Math.random() * 256),
		Math.floor(Math.random() * 256)];
};

var getTransparentColor = function (color, transp) {
	return "rgba(" + color[0] + "," + color[1] + "," +
                    color[2] + "," + transp + ")";
};

/**
 * HSV to RGB color conversion
 *
 * H runs from 0 to 360 degrees
 * S and V run from 0 to 100
 *
 * Ported from the excellent java algorithm by Eugene Vishnevsky at:
 * http://www.cs.rit.edu/~ncs/color/t_convert.html
 */
var hsvToRgb = function(h, s, v) {
	//source: http://snipplr.com/view/14590/hsv-to-rgb/
	var r, g, b;
	var i;
	var f, p, q, t;

	// Make sure our arguments stay in-range
	h = Math.max(0, Math.min(360, h));
	s = Math.max(0, Math.min(100, s));
	v = Math.max(0, Math.min(100, v));

	// We accept saturation and value arguments from 0 to 100 because that's
	// how Photoshop represents those values. Internally, however, the
	// saturation and value are calculated from a range of 0 to 1. We make
	// That conversion here.
	s /= 100;
	v /= 100;

	if(s == 0) {
		// Achromatic (grey)
		r = g = b = v;
		return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
	}

	h /= 60; // sector 0 to 5
	i = Math.floor(h);
	f = h - i; // factorial part of h
	p = v * (1 - s);
	q = v * (1 - s * f);
	t = v * (1 - s * (1 - f));

	switch(i) {
		case 0:
			r = v;
			g = t;
			b = p;
			break;

		case 1:
			r = q;
			g = v;
			b = p;
			break;

		case 2:
			r = p;
			g = v;
			b = t;
			break;

		case 3:
			r = p;
			g = q;
			b = v;
			break;

		case 4:
			r = t;
			g = p;
			b = v;
			break;

		default: // case 5:
			r = v;
			g = p;
			b = q;
	}

	return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

var randomColors = function(total) {
	//source: http://stackoverflow.com/a/6823364
	var i = 360 / (total - 1); // distribute the colors evenly on the hue range
	var r = []; // hold the generated colors
	for (var x=0; x<total; x++)
	{
		r.push(hsvToRgb(i * x, 100, 100)); // you can also alternate the saturation and value for even more contrast between the colors
	}
	return r;
};

var is_valid_period_range = function(y0,m0,y1,m1){
	return y0<y1 || (y0==y1 && m0<=m1)
}
var get_next_year_month_pair = function(y,m){
	next_year = y
	next_month = m+1
	if(next_month>12){
	    next_month = 1
	    next_year++
	}
	return [next_year, next_month]
}
var get_period_range = function(y0, m0, y1, m1){
	periods = []
	y = y0
	m = m0
	while( (y<y1) || (y==y1 && m<=m1)	){
		periods.push(y + "-" + m)
		ym_pair = get_next_year_month_pair(y,m)
		y = ym_pair[0]
		m = ym_pair[1]
	}
	console.log(periods)
	return periods
};