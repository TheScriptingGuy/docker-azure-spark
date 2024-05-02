Feature: Add columns
  Scenario: Add values from two columns
    Given a table value_table with the following records:
    | value1 | value2 | 
    | 1 | 2 |
    When I add value 1 and value 2
    Then a new column "sum" is created with the correct values:
    | value1 | value2 | sum |
    | 1 | 2 |   3 |