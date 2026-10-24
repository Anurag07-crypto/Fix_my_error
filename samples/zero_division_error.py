def average(nums):
    print("Calculating average for:", nums)
    if not nums:
        print("List is empty, so division is about to fail.")
    return sum(nums) / len(nums)


for scores in ([90, 85, 70], [], [100, 80, 60]):
    print("Current scores:", scores)
    print("Average:", average(scores))
