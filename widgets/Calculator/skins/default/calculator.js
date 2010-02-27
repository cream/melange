var lastcommand = '';
var lastnumber = '';
var actnumber = '';
var commands = new Array();
commands["+"] = "+";
commands["-"] = "-";
commands["&#247;"] = "/";
commands["&#215;"] = "*";
commands["&radic;"] = "SQRT";

function addnumber(num){
	actnumber = actnumber + num;
	if (document.getElementById('lcd').innerHTML == '0') {
		document.getElementById('lcd').innerHTML = actnumber;
	}
	else {
		document.getElementById('lcd').innerHTML += num;
	}
}

function reset(){
	lastcommand = '';
	lastnumber = '';
	actnumber = '';
	document.getElementById('lcd').innerHTML = '0';
}

function command(command){    
	// calculate the current
	lastnumber = calc(false);
	lastcommand = command;
	actnumber = '';
    if (command != 'SQRT') {
    	document.getElementById('lcd').innerHTML += command;
    }
    else {
        document.getElementById('lcd').innerHTML = '√' + document.getElementById('lcd').innerHTML;
    }
}

function calc(display){
    if (lastcommand != 'SQRT') {
    	sum = eval(lastnumber + lastcommand + actnumber);
    }
    else {
        sum = Math.sqrt(lastnumber);
    }
    if (display == true) {
    	document.getElementById('lcd').innerHTML = sum;
    }
	actnumber = sum;
	return sum;
}
