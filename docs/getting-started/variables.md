# Variables

Like many other programming languages, Z# supports the basic idea of a variable.

Now, Z# is a strongly-typed language, meaning that a variable must have a type which may not
be changed during execution.

To create a variable, we use the `var` statement.
```go
var my_variable = "Hello!";
```

In the above example, the variable `my_variable` has the **inferred** type `String`, which
is a built-in type.

When we want to use the variable we created, we can refer to it by its name.

```go
print(my_variable);  // Output: Hello!
```

We can also reassign variable values with the assignment operator (`=`)
```go
my_variable = "Bye!";

print(my_variable); // Output: Bye!
```

Since `my_variable` has a type `String`, trying to assign any other type will result
with an error.
```go
my_variable = 1;  // Error. Can't assign type `i32` to type `String`.
```
