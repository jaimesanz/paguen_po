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
}

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