## 1.测试场景 a：用户明确提供身份
User 1: I am a junior student and would like to review papers on learned indexes.

System: Your identity has been identified as Junior Student, and your task is Reviewing papers. Here are the recommended questions:

Recommended questions: ['What is the main idea of the paper "The Case for Learned Index Structures" by Kraska et al.?', 'Can you summarize the key contributions of this paper in simple terms?', 'What are the main datasets used in the experiments of this paper?', 'What are the evaluation metrics used to compare learned indexes with traditional indexes like B-trees?', 'The paper mentions neural networks for indexing. Can you explain how they use neural networks in this context?', 'Are there any specific limitations of learned indexes mentioned in the paper that I should note for my review?', 'Can you suggest a few beginner-friendly resources to understand the background concepts of learned indexes?']

## 2.测试场景 b：用户仅提问，需要进一步询问用户明确身份
User 2: Can you identify gaps in current research on learned indexes for time-series databases?

System: We are unable to verify your researcher levels. Which of the following applies to you? 
Options: Junior Student, Senior Student, Post-Doc, Professor。

User 2: I am a senior student.

System (followed): Thank you for your response. Your identity has been confirmed as Senior Student and your task is Reviewing papers. Here are the recommended questions:

Recommended questions: ['What is the problem statement in the paper "Learned Indexes for Dynamic Workloads" by Ding et al.?', 'How does the paper address the challenge of handling dynamic data in learned indexes compared to static data?', 'What assumptions does the paper make about the data distribution for its learned index model?', 'Can you identify any potential biases in the experimental setup of this paper?', 'How does the paper compare the performance of its learned index against traditional indexing methods like hash tables?', 'What are the main criticisms or limitations of the proposed approach as discussed in the paper or related works?', 'Can you help me draft a critical question about the scalability of their approach for my class discussion?']

## 3. 测试场景 c: 其他研究领域下用户提问
User 3: How can we compare the performance of different knowledge graph methods in recommender systems?

System: We are unable to verify your researcher levels. Which of the following applies to you? 
Options: Junior Student, Senior Student, Post-Doc, Professor。

User 3: I am a senior student.

System (followed): Thank you for your response. Your identity has been confirmed as Senior Student and your task is Reviewing papers. Here are the recommended questions:

Recommended questions: ['What is the problem statement in the paper "Learned Indexes for Dynamic Workloads" by Ding et al.?', 'How does the paper address the challenge of handling dynamic data in learned indexes compared to static data?', 'What assumptions does the paper make about the data distribution for its learned index model?', 'Can you identify any potential biases in the experimental setup of this paper?', 'How does the paper compare the performance of its learned index against traditional indexing methods like hash tables?', 'What are the main criticisms or limitations of the proposed approach as discussed in the paper or related works?', 'Can you help me draft a critical question about the scalability of their approach for my class discussion?']
