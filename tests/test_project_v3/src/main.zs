import { print } from Python;

fun print2(value) {
    print(value);

    return 0;
}

fun no_print() {
    print("this should not print");
}

{
    print("Block!");
}

if (true) {
    print("TRUE, NO ELSE");
}

if (true) {
    print("TRUE");
} else {
    no_print();
}

if (false) {
    no_print();
} else {
    print("ELSE");
}

print2("Hello, Z#!");
print2(2);
print2(2.2);

fun get(x) {
    return x;
}

{
    fun BLOCK() {}
}

print(get("GET!"));


while (true) {
    print("while true!");
    break;
}


while (false) {
    no_print();
}

while A(true) {
    print("A begin");

    while (true) {
        print("Inner");

        break A;
    }

    no_print();
}


while (false) {

} else {
    print("WHILE ELSE SUCCESS!");
}


while (true) {
    break;
} else {
    no_print();
}

while A(true) {
    while (true) {
        break A;
    } else {
        no_print();
    }
} else {
    no_print();
}

while (false) no_print();
else print("WHILE ELSE SUCCESS");

if (true) print("IF SUCCESS");
else if (false) no_print();
else no_print();

if (false) no_print();
else if (true) print("ELSE IF SUCCESS");
else no_print();

if (false) no_print();
else if (false) no_print();
else print("IF ELSE IF ELSE SUCCESS");


when (1) {
case (1) print("ONE");
} else no_print();

when (1) {
case (2) no_print();
case (3) no_print();
} else print("WHEN ELSE SUCCESS");

when (1) {
case (1) print("ONE");
case (2) no_print();
case (1) no_print();
}

when (1) {
case (2) no_print();
case (1) { print("ONE"); continue; }
case (2) { print("WHEN CONTINUE SUCCESS"); }
case (3) no_print();
} else no_print();