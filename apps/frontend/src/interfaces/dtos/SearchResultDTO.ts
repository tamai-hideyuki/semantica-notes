export interface SearchResultDTO {
    uuid:       string;
    title:      string;
    snippet:    string;
    body:       string;
    category:   string;
    tags:       string[];
    created_at: string;
    score:      number;
}
