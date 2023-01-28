# Functions

One of the most basic building blocks of any program is a function.

In order to define a function in Z#, we use the `fun` keyword (because functions are fun!).

```go
fun my_function() {

}
```

The above function is empty, so it doesn't do much. Let's try and create a function to greet the user.

```go
fun greet() {
    print("Hello user!");
}
```


Running the code now will not do anything, and that's because defining a function is not enough.
We also need to **call** it. Calling a function in Z# is easy enough. Just use the call operator (`()`).
```go
greet();  // Output: Hello user!
```

If you were paying attention, you'd notice that `print` is also a function, thus we can use the call 
operator on it as well!

This function is not so useful tho, we want to be able to use it for different people as well, not just
people who's name is `user`...

That's why we need *parameters*.
In Z#, we can define parameters in the parameter list of the function definition.
```go
fun greet(user) {
    print("Hello " + user "!");  // (1)!
}

greet("Benjo"); // Output: Hello Benjo!
```

1. The (`+`) operator is not yet supported for anything, so this will actually result with an internal error.
