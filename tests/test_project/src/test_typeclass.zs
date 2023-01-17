import { print, create_instance_of } from Python;
import { Foo } from "src/main.zs";


typeclass IPrint {
    fun print();
}


typeclass IPrint(Foo) {
    fun print() {
        Foo.baz();
    }
}


fun do_print(x: IPrint)
{
    x.print();
}

do_print(create_instance_of(Foo));
