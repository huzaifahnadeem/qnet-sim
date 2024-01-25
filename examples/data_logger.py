
class DataLogger:
    def __init__(self, labels) -> None:
        self.labels = labels
        self.data_table = {}
        for l in labels:
            self.data_table[l] = []

    def add_data_point(self, data_row):
        for i in range(len(data_row)):
            self.data_table[self.labels[i]].append(str(data_row[i]))

    # def print_data_table(self):
    #     print(f'{self.x_label}\t{self.y_label}')
    #     print(f'-------------------')
    #     for i in range(len(self.data_table[self.x_label])):
    #         print(f'{self.data_table[self.x_label][i]}\t{self.data_table[self.y_label][i]}')
    
    def save_data_csv(self, name):
        # header = f'{self.x_label},{self.y_label}'
        # lines = []
        # lines.append(header)
        # for i in range(len(self.data_table[self.x_label])):
        #     lines.append(f'{self.data_table[self.x_label][i]},{self.data_table[self.y_label][i]}')

        # with open(f'./examples/{name}', 'w') as f:
        #     # Use a for loop to write each line of data to the file
        #     for l in lines:
        #         f.write(l + '\n')

        header = ','.join(self.labels)
        lines = [header]
        for i in range(len(self.data_table[self.labels[0]])):
            this_line = ''
            for l in self.labels:
                this_line += self.data_table[l][i] + ','
            lines.append(this_line[:-1])
        # with open(f'./examples/{name}', 'w') as f:
        with open(f'{name}', 'w') as f:
            for l in lines:
                f.write(l + '\n')
