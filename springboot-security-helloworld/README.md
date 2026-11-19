# Spring Boot 3.2.0 HelloWorld with Spring Security

A minimal Spring Boot 3.2.0 project providing:

- `GET /hello` -- returns the string `Hello World`, requires Spring Security authentication.
- Username-password login (`test` / `123456`) -- provided by Spring Security's built-in form login (`GET /login` shows the generated login page, `POST /login` performs the login).

## Tech Stack

- Java 17
- Spring Boot 3.2.0
- Spring Security 6 (built-in session-based form login)
- Maven

## Build & Run

```bash
# Build
mvn clean package

# Run
mvn spring-boot:run
# or
java -jar target/springboot-security-helloworld-1.0.0.jar
```

The server starts on `http://localhost:8080`.

## How It Works

- Every request requires authentication (`anyRequest().authenticated()`).
- Unauthenticated requests to `/hello` are redirected (HTTP 302) to the auto-generated login page at `GET /login`.
- `POST /login` with `username=test` / `password=123456` authenticates the user; the session id is kept in a `JSESSIONID` cookie, so no token handling is needed.
- Passwords are stored with BCrypt. The user is kept in memory via `InMemoryUserDetailsManager`.

### Try it in the browser

1. Open `http://localhost:8080/hello` -- you are redirected to the login page.
2. Enter `test` / `123456` -- you are redirected back to `/hello`, which shows `Hello World`.

### Try it with curl

```bash
# Unauthenticated request -> 302 redirect to the login page
curl -i http://localhost:8080/hello
# -> HTTP/1.1 302, Location: http://localhost:8080/login

# Login: stores the session cookie in cookies.txt, response is a redirect to "/"
curl -i -c cookies.txt -X POST http://localhost:8080/login \
  -d "username=test&password=123456"

# Access /hello with the session cookie
curl -b cookies.txt http://localhost:8080/hello
# -> Hello World
```

## Tests

```bash
mvn test
```

Covers: redirect to the login page when unauthenticated, login page availability, failed login, and session-based login followed by `Hello World`.
