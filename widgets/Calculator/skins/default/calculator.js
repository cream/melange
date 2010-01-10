var lastcommand = ''
var lastnumber = ''
var actnumber = ''

function addnumber(num){
	actnumber = actnumber + num
	document.getElementById('lcd').innerHTML = actnumber
}

function reset(){
	lastcommand = ''
	lastnumber = ''
	actnumber = ''
	document.getElementById('lcd').innerHTML = '0'
}

function command(command){
	lastcommand = command
	lastnumber = actnumber
	actnumber = ''
	document.getElementById('lcd').innerHTML = '0'
}

function calc(){
	sum = eval(lastnumber + lastcommand + actnumber)
	document.getElementById('lcd').innerHTML = sum
	actnumber = sum
}
