# this is 20x-30x slower than c...
.function fibo
.args n
.locals t1, t2
	blti	n, 2, L_base_case
	addi	t1, n, -1
	call	t1, fibo, t1, 1
	addi 	t2, n, -2
	call 	t2, fibo, t2, 1
	add	n, t1, t2
	label	L_base_case
	ret n
.endfunction

.function add
.args a, b
	add a, a, b
	ret a
.endfunction

.function loop
.args n
	ret n # stub
.endfunction

.function main
.locals n
	movei	n, 35
	call	n, fibo, n, 1
	print	n
	halt
.endfunction

