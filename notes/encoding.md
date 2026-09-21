1. Encoding

Encoding is the process of converting categorical data, such as text or labels, into numerical values so that a machine-learning model can understand and process it. Most ML algorithms perform mathematical calculations, so they cannot directly work with values like "Male", "Female", "Delhi", or "Mumbai". Encoding converts these categorical values into a numerical representation. There are different types of encoding, and the appropriate method depends on whether the categories have a meaningful order or not.

Example: Suppose we have an Education column:

School
College
University

Since these categories have a natural order, we can use Ordinal Encoding.

⸻

2. Ordinal Encoding

Ordinal Encoding converts categorical values into numbers while preserving the order or ranking between the categories. It is appropriate when the categories have a meaningful hierarchy. For example, if we have Low, Medium, and High, we can represent them as 0, 1, and 2. The numbers are not just labels; they represent the fact that Low < Medium < High. However, ordinal encoding should generally not be used for categories that have no natural order because the model may incorrectly interpret the numerical values as having a meaningful relationship.

Example:

Education
School       → 0
College      → 1
University   → 2

Here, 2 represents a higher education level than 1, so ordinal encoding makes sense.

⸻

3. One-Hot Encoding

One-Hot Encoding converts categorical values into multiple binary columns containing 0 and 1. It is mainly used when categories do not have any natural order. Instead of assigning numbers such as 0, 1, and 2—which could make the model think one category is greater than another—one-hot encoding creates a separate column for each category. A value of 1 indicates that the observation belongs to that category, while 0 indicates that it does not.

Example: Suppose we have:

City
Delhi
Mumbai
Chennai

One-hot encoding produces:

City	Delhi	Mumbai	Chennai
Delhi	1	0	0
Mumbai	0	1	0
Chennai	0	0	1

Here, we don’t say that Mumbai is “greater than” Delhi, so one-hot encoding is appropriate.

Easy rule:

* Ordered categories → Ordinal Encoding
* Unordered categories → One-Hot Encoding

⸻

4. StandardScaler

StandardScaler is used to standardize numerical features so that they have approximately a mean of 0 and a standard deviation of 1. This is important when different features have very different scales. For example, if Age ranges from 18–60 but Salary ranges from 20,000–200,000, the larger numerical values of Salary can disproportionately affect algorithms that depend on distances or gradient calculations. StandardScaler transforms each value using the formula:

z = (x - mean) / standard deviation

Example: Suppose the ages are:

20, 30, 40

The scaler calculates their mean and standard deviation and transforms each age into a standardized value. The resulting values are centered around 0 rather than remaining on the original 20–40 scale.

StandardScaler is particularly useful for algorithms such as KNN, SVM, Logistic Regression, Linear Regression, PCA, and neural networks. It is generally less important for tree-based models such as Decision Trees and Random Forests.

⸻

5. fit()

fit() means learn the required information from the training data. It does not actually transform the data. For example, when we use StandardScaler, fit() calculates the mean and standard deviation of each feature from the training dataset. Similarly, when we use an encoder, fit() learns the categories present in the training data.

scaler.fit(X_train)

This means:

“Look at X_train and learn what parameters you need.”

For StandardScaler, it learns:

mean
standard deviation

⸻

6. transform()

transform() uses the information learned during fit() to actually modify the data.

scaler.transform(X_train)

So:

fit()       → learn
transform() → apply what was learned

For example:

scaler.fit(X_train)
X_train_scaled = scaler.transform(X_train)

The scaler first learns the mean and standard deviation from X_train, and then uses those values to standardize X_train.

⸻

7. fit_transform()

fit_transform() simply combines fit() + transform() into one operation.

Instead of writing:

scaler.fit(X_train)
X_train_scaled = scaler.transform(X_train)

you can write:

X_train_scaled = scaler.fit_transform(X_train)

So remember:

fit()            → Learn
transform()      → Apply
fit_transform()  → Learn + Apply

The most important ML rule

For your training data:

X_train = scaler.fit_transform(X_train)

For your test data:

X_test = scaler.transform(X_test)

Do NOT do this:

X_test = scaler.fit_transform(X_test)

because you don’t want the scaler to learn new mean and standard deviation from the test data. You want the test data to be transformed using the parameters learned from the training data. This helps prevent data leakage.

One-line memory trick

Encoding converts categories → numbers, StandardScaler puts numerical features on a common scale, fit() learns, transform() applies, and fit_transform() does both.
