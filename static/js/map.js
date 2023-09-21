var canvas = document.querySelector("#cnv");
const ctx = canvas.getContext("2d");
// var cords = document.querySelector('#cords')

// var timer = document.querySelector('#timer');

// var last_time = new Date(last_time_iso);

var gg = localStorage.getItem('gg')

// setInterval(update_map, 3000);
// setInterval(update_time, 1000); 
update_map();

var mouse = {
  moved: false,
  press: false,
  start_pos: { x: 0, y: 0 },
};
var canvas_size = Math.min(window.innerHeight, window.innerWidth) * 0.9;
var grid_color = "rgb(20, 24, 51)";
var grid = 100;
var cnv_bg = "#161829";
var cursor_color = "rgb(143, 150, 248)";

let cameraOffset = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
let cameraZoom = 1;
let MAX_ZOOM = 20;
let MIN_ZOOM = 0.8;
var move_x = 0;
var move_y = 0;
let SCROLL_SENSITIVITY = 0.0005;
var phone = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
var setk = false;


// window.addEventListener('resize', resizeCanvas, false);
// function resizeCanvas() {

//     canvas.height =  window.innerHeight;
//     canvas.width = window.innerWidth;
// }
// resizeCanvas();

function rect(x, y, w, h, c, alpha = 1) {
	ctx.globalAlpha = alpha;
	ctx.fillStyle = c;
	ctx.fillRect(x, y, w, h);
	ctx.globalAlpha = 1.0;
}

class Cursor {
	constructor(x, y) {
		this.x = x;
		this.y = y;
		this.i = 0;
		this.j = 0;
	}
	draw() {
		rect(this.x, this.y, (canvas_size / grid) - (setk ? 1 : 0), (canvas_size / grid) - (setk ? 1 : 0), "#808080",  0.5);
	}
}

class Cell {
	constructor(i, j, c) {
		this.i = i;
		this.j = j;
		this.w = canvas_size / grid;
		this.x = (i * this.w + 2) - (canvas_size / 2);
		this.y = (j * this.w + 2) - (canvas_size / 2);
		this.c = c
		this.changeColor();
		this.draw();
	}
	draw() {
		rect(
			this.x,
			this.y,
			this.w - (setk ? 1 : 0),
			this.w - (setk ? 1 : 0),
			this.color
		);
		// if(this.active){
		//     ctx.fillStyle = grid_color;
		//     ctx.fillRect(null_pos.x + (this.x * size_cell), null_pos.y + (this.y * size_cell), size_cell, size_cell);
		//     ctx.fillStyle = this.color;
		//     ctx.fillRect(null_pos.x + (this.x * size_cell) + 0.5, null_pos.y + (this.y * size_cell) + 0.5, size_cell - 1, size_cell - 1);
		// }
	}
	changeColor(color = this.c){
		this.color = color;
	}
	checkMouse(x, y) {
		return (
		x > this.x && x < this.x + this.w && y > this.y && y < this.y + this.w
		);
	}
}

class Map {
	constructor() {
		this.cursor = new Cursor(0, 0, cursor_color);
		// this.cells = ;
		this.cells = Array(grid).fill().map((j, y) => (j = Array(grid).fill().map(
			(i, x)=>{
				return new Cell(x, y, 'white');
			}
		)));
		this.selected_color = '#FFA500';
	}
}

function setColor(color){
	document.documentElement.style.setProperty("--clr-select", color);
	map.selected_color = color;
}

var map = new Map();
var cursor = new Cursor(0, 0);

// TEST

// var test_map = new Map();
// for(let i = 0; i < 50; i++){
//     for(let j = 0; j < 50;j++){
//         let test_cell = new Cell(i, j, 'white');
//         test_map.add_cell(test_cell);
//     }

// }
// test_map.draw();
let isDragging = false;
let dragStart = { x: 0, y: 0 };

function getEventLocation(e) {
	if (e.touches && e.touches.length == 1) {
		return { x: e.touches[0].clientX, y: e.touches[0].clientY };
	} else if (e.clientX && e.clientY) {
		return { x: e.clientX, y: e.clientY };
	}
}

function onPointerDown(e) {
	isDragging = true;
	dragStart.x = getEventLocation(e).x / cameraZoom - cameraOffset.x;
	dragStart.y = getEventLocation(e).y / cameraZoom - cameraOffset.y;
	click_x = getEventLocation(e).x;
	click_y = getEventLocation(e).y;
}

function onPointerUp(e) {
	isDragging = false;
	initialPinchDistance = null;
	lastZoom = cameraZoom;
	if (
		Math.abs(click_x - getEventLocation(e).x) < 6 &&
		Math.abs(click_y - getEventLocation(e).y) < 6 &&
		move_x < canvas_size / 2 &&
		move_y < canvas_size / 2
	) {
		click(e);
	}
}

function onPointerMove(e) {
	if (isDragging) {
		cameraOffset.x = getEventLocation(e).x / cameraZoom - dragStart.x;
		cameraOffset.y = getEventLocation(e).y / cameraZoom - dragStart.y;
	}
	move_x = (getEventLocation(e).x - window.innerWidth / 2) / cameraZoom + window.innerWidth / 2 - cameraOffset.x;
	move_y = (getEventLocation(e).y - window.innerHeight / 2) / cameraZoom + window.innerHeight / 2 - cameraOffset.y;
}

function handleTouch(e, singleTouchHandler) {

	if (event.scale !== 1) { event.preventDefault(); }
	if (e.touches.length == 1) {
		singleTouchHandler(e);
	} else if (e.type == "touchmove" && e.touches.length == 2) {
		isDragging = false;
		handlePinch(e);
	}
}

let initialPinchDistance = null;
let lastZoom = cameraZoom;

function adjustZoom(zoomAmount, zoomFactor)
{
    if (!isDragging)
    {
        if (zoomAmount)
        {
            cameraZoom += zoomAmount
        }
        else if (zoomFactor)
        {
            cameraZoom = zoomFactor*lastZoom
        }
        cameraZoom = Math.min( cameraZoom, MAX_ZOOM )
        cameraZoom = Math.max( cameraZoom, MIN_ZOOM )
    }
}

function handlePinch(e) {
	e.preventDefault();

	let touch1 = { x: e.touches[0].clientX, y: e.touches[0].clientY };
	let touch2 = { x: e.touches[1].clientX, y: e.touches[1].clientY };

	// This is distance squared, but no need for an expensive sqrt as it's only used in ratio
	let currentDistance = (touch1.x - touch2.x) ** 2 + (touch1.y - touch2.y) ** 2;

	if (initialPinchDistance == null) {
		initialPinchDistance = currentDistance;
	} else {
		adjustZoom(null, currentDistance / initialPinchDistance);
	}
}

function callAll(callback, reverse) {
	if (reverse)
		for (var i = grid - 1; i >= 0; i--)
		for (var j = grid - 1; j >= 0; j--) {
			callback(map.cells[j][i], i, j);
		}
	else
		for (var i = 0; i < grid; i++)
		for (var j = 0; j < grid; j++) {
			callback(map.cells[j][i], i, j);
		}
}

function click(e){
	// now_x = ((getEventLocation(e).x - (window.innerWidth / 2))/cameraZoom) + (window.innerWidth / 2)  - cameraOffset.x;
	// now_y = ((getEventLocation(e).y - (window.innerHeight / 2))/cameraZoom) + (window.innerHeight / 2)  - cameraOffset.y;
	// callAll((item) => {
	// 	if(item != undefined){
	// 		if(item.checkMouse(now_x, now_y)){
	// 			cursor.y = item.y;
	// 			cursor.x = item.x;
	// 			cursor.i = item.i;
	// 			cursor.j = item.j;
	// 		}
	// 	}
	// });

	// console.log(cursor.i, cursor.j);

	// fetch('/click', {
	// 	method: "post",
	// 	headers: {
	// 		'Accept': 'application/json',
	// 		'Content-Type': 'application/json'
	// 	},
	// 	body: JSON.stringify({
	// 		x: cursor.i,
	// 		y: cursor.j,
	// 		color: map.selected_color,
	// 	})
	// }).then((req)=>{
	// 	req.json().then((res)=>{
	// 		if(res.ok){
	// 			map.cells[res.params.y][res.params.x].color = res.params.color;
	// 			last_time = new Date();
	// 		}else{
	// 			console.log(res.result);
	// 			if(res.last_time){
	// 				last_time = new Date(res.last_time);
	// 			}
	// 		}
	// 	})
	// });
	
}

// function update_time(){
// 	let must_be = new Date().setTime(last_time.getTime() + 1 * 60 * 1000);
// 	if(must_be > new Date()){
// 		let microsec = must_be - new Date();
// 		let minutes_str = `${Math.floor(microsec / 1000 / 60)}`;
// 		let seconds_str = `${Math.floor((microsec - (Math.floor(microsec / 1000 / 60) * 1000 * 60)) / 1000)}`
// 		minutes_str = minutes_str.length == 1 ? '0' + minutes_str : minutes_str
// 		seconds_str = seconds_str.length == 1 ? '0' + seconds_str : seconds_str

// 		timer.innerHTML = `${minutes_str}:${seconds_str}`;
// 	}else{
// 		timer.innerHTML = `access`;
// 	}
		
// }

function update_map(){
	fetch('', {
		method: "post",
		headers: {
			'Accept': 'application/json',
			'Content-Type': 'application/json'
		},
	}).then(
		(res) =>{
			res.json().then((res_json)=>{
				if(res_json.ok){
					let res_map = res_json.map;
					res_map.forEach((row, y) => {
						row.forEach((element, x)=>{
							map.cells[y][x].color = element;
						})
					});

				}
			})
		}
	)
}

function draw() {
	canvas.width = window.innerWidth;
	canvas.height = window.innerHeight;

	ctx.translate(window.innerWidth / 2, window.innerHeight / 2);
	ctx.scale(cameraZoom, cameraZoom);

	ctx.translate(
		-window.innerWidth / 2 + cameraOffset.x,
		-window.innerHeight / 2 + cameraOffset.y
	);
	ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

	rect(
		-(canvas_size / 2),
		-(canvas_size / 2),
		canvas_size + 4,
		canvas_size + 4,
		"#a1e7fb"
	);

	callAll((item)=>{
		if(item != undefined){
			item.draw();
			if(item.checkMouse(move_x, move_y)){
				cursor.y = item.y;cursor.x = item.x;
				cursor.i = item.i;cursor.j = item.j;
			}
		}
	});
	
	// if(!phone){
	// 	cords.innerHTML = `x: ${cursor.i}, y:  ${cursor.j}`
	// }else{
	// 	cords.innerHTML = '';
	// }
	

	if(false){
		cursor.draw();
	}

	requestAnimationFrame(draw);

	if(!gg){
		alert('PixelBattle закончился, спасибо всем кто принимал участие!!!');
		localStorage.setItem('gg', true);
		gg = true;
	}
}

canvas.addEventListener("mousedown", onPointerDown);
canvas.addEventListener("touchstart", (e) => handleTouch(e, onPointerDown));
canvas.addEventListener("mouseup", onPointerUp);
canvas.addEventListener("touchend", (e) => handleTouch(e, onPointerUp));
canvas.addEventListener("mousemove", onPointerMove);
canvas.addEventListener("touchmove", (e) => handleTouch(e, onPointerMove));
canvas.addEventListener("wheel", (e) =>
  adjustZoom(-e.deltaY * SCROLL_SENSITIVITY)
);

draw();