# Machine Learning Concepts
## 1. Supervised Learning
Supervised Learning is a type of machine learning where the model is trained using data that already has a known target/output (label). The model learns the relationship between the input features `X` and the target `y`, and after learning this relationship, it can predict the target for new, unseen data. Supervised learning is mainly divided into **classification** and **regression**. In classification, the target is a category such as Yes/No, Spam/Not Spam, or Disease/No Disease, whereas in regression, the target is a numerical value such as Salary, House Price, or Temperature.
### Example
Suppose we have information about houses such as area, number of bedrooms, and location, along with their actual selling prices. The model learns from these examples and then predicts the price of a new house. Since the actual prices are already available during training, this is supervised learning.
---
## 2. Unsupervised Learning
Unsupervised Learning is a type of machine learning where the model is given data without a target/output label. Instead of learning to predict a known answer, the model tries to discover hidden patterns, structures, or groups within the data by itself. Common unsupervised-learning techniques include **clustering**, such as K-Means, and **dimensionality reduction**, such as PCA. Since there is no predefined correct output, the goal is generally to understand the structure of the data rather than directly predict a target.
### Example
Suppose an e-commerce company has customer information such as spending amount, number of purchases, and browsing activity, but there is no predefined customer category. K-Means can analyze the data and group customers with similar behavior into different clusters. The company might then discover groups such as frequent high-spending customers and occasional low-spending customers.
### Easy Difference
- **Supervised** = Data + Answers → Learn to predict
- **Unsupervised** = Data without answers → Find patterns/groups
---
## 3. Linear Regression
Linear Regression is a supervised learning algorithm used for **regression problems**, where the target variable is a continuous numerical value. It tries to find the best-fitting straight line between the input features and the target so that it can predict numerical values.
In simple linear regression with one feature, the model can be represented as:
$$
\hat{y} = b_0 + b_1x
$$
Where:
- `b₀` = intercept
- `b₁` = coefficient or slope
- `x` = input
- `ŷ` = predicted value
The model learns the values of `b₀` and `b₁` by trying to minimize the prediction errors, commonly using the **least-squares method**.
### Example
Suppose we want to predict a student's salary based on their years of experience. We may have data such as:
| Experience | Salary |
|---|---:|
| 1 year | ₹30,000 |
| 2 years | ₹40,000 |
| 3 years | ₹50,000 |
| 5 years | ₹70,000 |
Linear Regression learns the relationship between experience and salary and may predict that someone with **4 years of experience earns around ₹60,000**.
### Important Point
> **Linear Regression → predicts a continuous numerical value.**
### Examples of Regression Targets
- House Price
- Salary
- Temperature
- Sales
- Age
---
## 4. Logistic Regression
Despite its name, **Logistic Regression is primarily a classification algorithm**, not a regression algorithm. It is commonly used when the target is a categorical outcome, particularly **binary classification**, such as Yes/No, 0/1, or Spam/Not Spam.
Instead of directly producing an unrestricted numerical prediction like Linear Regression, Logistic Regression calculates a **probability between 0 and 1** using the **sigmoid function**. A threshold is then used to convert that probability into a class.
For example:
- Probability ≥ `0.5` → Class `1`
- Probability < `0.5` → Class `0`
### Example
Suppose we want to predict whether a student will pass or fail based on the number of hours they studied.
| Hours Studied | Result |
|---:|---|
| 2 | Fail |
| 3 | Fail |
| 5 | Pass |
| 7 | Pass |
| 9 | Pass |
Logistic Regression learns the relationship between study hours and the probability of passing.
Suppose for a student who studied 7 hours, the model produces:

Probability of passing = 0.90

Since 0.90 is greater than the typical threshold of 0.5, the model predicts:

Pass → 1

If another student gets:

Probability of passing = 0.20

the model predicts:

Fail → 0

⸻

Linear vs Logistic Regression

Feature	Linear Regression	Logistic Regression
Type	Supervised	Supervised
Used for	Regression	Classification
Output	Continuous number	Probability → Class
Example	Predict salary	Predict pass/fail
Target	₹50,000, ₹70,000, etc.	0/1, Yes/No
Main idea	Fits a line	Uses sigmoid to get probability

Easy Memory Trick

Linear Regression → “How much?”
Logistic Regression → “Which class?”

For Example

House price = ₹80 lakh       → Linear Regression
House will sell? Yes/No      → Logistic Regression
